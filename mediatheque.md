# Comprendre l'articulation des fichiers de « Ma médiathèque »

*Tutoriel sur l'application Flask de gestion de livres, de CD et de DVD : qui fait quoi, et comment les fichiers se parlent.*

## 1. L'idée générale

L'application repose sur un principe simple : **chaque fichier a un seul métier**.

- <span style="color: royalblue;">models.py</span> décrit les **données** (les tables de la base).
- <span style="color: royalblue;">app.py</span> est le **chef d'orchestre** : il reçoit les requêtes du navigateur, lit ou écrit dans la base, puis choisit la page à afficher.
- <span style="color: royalblue;">template/</span> contient le **HTML** (avec des trous que Flask remplit).
- <span style="color: royalblue;">static/css/style.css</span> contient l'**apparence**.
- <span style="color: royalblue;">instance/mediatheque.db</span> contient les **données réelles** (le fichier SQLite).

Quand tu cliques sur un lien, le navigateur envoie une URL à <span style="color: royalblue;">app.py</span>. Celui-ci interroge la base grâce aux classes de
<span style="color: royalblue;">models.py</span>, injecte le résultat dans un template, et renvoie une page HTML qui va elle-même chercher le fichier CSS.

---

## 2. L'arborescence : qui fait quoi

```
mediatheque/
├── app.py                  ← routes + logique
├── models.py               ← tables Livre, Cd, Dvd
├── requirements.txt        ← Flask, Flask-SQLAlchemy
├── README.md               ← aide-mémoire de commandes
├── .gitignore              ← fichiers ignorés par Git
├── instance/
│   └── mediatheque.db      ← la base SQLite
├── templates/
│   ├── base.html           ← squelette commun
│   ├── index.html          ← page d'accueil
│   └── liste.html          ← page liste + formulaire (3 types)
└── static/
    └── css/
        └── style.css       ← feuille de style
```

| Fichier | Rôle | Avec qui il est lié |
| --- | --- | --- |
| `app.py` | Configuration, dictionnaire `TYPES`, routes | Importe `models.py` ; appelle les templates avec `render_template` |
| `models.py` | Objet `db` et classes `Livre`, `Cd`, `Dvd` | Importé par `app.py` ; ignore totalement les routes et le HTML |
| `templates/base.html` | En-tête, menu, messages flash, lien vers le CSS | Hérité par `index.html` et `liste.html` |
| `templates/index.html` | Accueil avec les trois « dos de livres » | Étend `base.html` |
| `templates/liste.html` | Formulaire + tableau, pour les trois types | Étend `base.html` ; reçoit ses données depuis `app.py` |
| `static/css/style.css` | Couleurs, mise en page | Chargé par `base.html` |
| `instance/mediatheque.db` | Les livres, CD et DVD enregistrés | Ouvert par SQLAlchemy via la configuration de `app.py` |
| `requirements.txt` | Liste des paquets à installer | Utilisé par `pip install -r requirements.txt` |

**Fichiers présents dans le dossier mais qui ne font pas partie de l'application :**

- `.venv/` (environnement virtuel), `__pycache__/` (cache Python) et `.git/` (historique Git) : générés automatiquement.
- `me` : un fichier vide, sans doute créé par accident.
- `podman.txt` : note (PostgreSQL) sans rapport avec la médiathèque.

---

## 3. Le trajet d'une requête, de bout en bout

Prenons l'affichage de la page des livres, à l'adresse `/livres` :

1. Le navigateur envoie `GET /livres`.
2. Flask compare l'URL à ses routes dans `app.py` et choisit la fonction `liste`, avec `type_ = 'livres'`.
3. `liste` récupère la description du type : `t = TYPES['livres']`.
4. `chercher(t, q)` utilise `t['model']`, c'est-à-dire la classe `Livre` de `models.py`, pour interroger la table `livre` de `mediatheque.db`. SQLAlchemy renvoie une liste d'objets `Livre`.
5. `render_template('liste.html', ...)` envoie à Jinja les variables `type_`, `t`, `elements`, `element` et `q`.
6. `liste.html` étend `base.html` : Jinja fusionne les deux fichiers et remplit les trous avec les variables.
7. Le HTML complet part vers le navigateur. Il contient une balise `<link>` vers `/static/css/style.css` : le navigateur télécharge ce fichier et applique le style.

Retiens cette chaîne : **URL → route (app.py) → modèle (models.py) → base → template → CSS**.

---

## 4. <span style="color: dodgerblue;">models.py</span> : les données

```python
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Livre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    ...
```

- `db = SQLAlchemy()` crée l'objet qui fait le lien avec la base. Il est créé **sans application** : c'est `app.py` qui le rattachera à Flask plus tard.
- Chaque classe qui hérite de `db.Model` devient une **table**. SQLAlchemy déduit le nom de la table du nom de la classe : `Livre` → `livre`, `Cd` → `cd`, `Dvd` → `dvd`.
- Chaque `db.Column(...)` devient une **colonne**. `nullable=False` sur `titre` signifie que le titre est obligatoire au niveau de la base.

**Pourquoi ce fichier est séparé de `app.py` ?** `app.py` importe `models.py`, mais `models.py` n'importe jamais `app.py`. Cela évite un « import circulaire » et garde les données indépendantes du reste.

**Le pacte entre les fichiers :** les trois classes ont toutes une colonne `titre`. C'est ce qui permet à la fonction `chercher` de trier tous les types avec `modele.titre`. Si tu supprimais `titre` d'une classe, la liste correspondante planterait.

---

## 5. <span style="color: dodgerblue;">app.py</span> : le chef d'orchestre

### 5.1 La configuration

```python
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mediatheque.db'
app.config['SECRET_KEY'] = 'changez-moi'
db.init_app(app)
```

- `SQLALCHEMY_DATABASE_URI` indique où se trouve la base. Avec SQLite et Flask-SQLAlchemy, le fichier est créé dans le dossier `instance/`.
- `SECRET_KEY` sert à signer la session, dont dépendent les messages `flash()` (« Enregistré. »).
- `db.init_app(app)` est le **point de jonction** : c'est ici que l'objet `db` de `models.py` est relié à l'application.

### 5.2 Le dictionnaire `TYPES` : le cœur du système

Plutôt que d'écrire trois fois le même code (livres, CD, DVD), `app.py` décrit chaque type dans un dictionnaire. Chaque entrée contient :

| Clé | Contenu | Qui l'utilise |
| --- | --- | --- |
| `model` | La classe SQLAlchemy (`Livre`, `Cd`, `Dvd`) | `chercher`, `ajouter`, `modifier`, `supprimer` |
| `nom` | Nom affiché au pluriel | `liste.html` (titre de l'onglet) |
| `page` | Titre de la page | `liste.html` (le `<h1>`) |
| `un` | « un livre », « un CD »… | `liste.html` (« Ajouter un livre ») |
| `recherche` | Colonnes interrogées par la recherche | `chercher` |
| `champs` | Champs du formulaire | `lire_formulaire` **et** `liste.html` (qui dessine le formulaire) |
| `colonnes` | Colonnes du tableau | `liste.html` (en-têtes et cellules) |

La petite fonction `champ(nom, label, type, options, plein)` sert seulement à fabriquer proprement chaque dictionnaire de champ.

**C'est ce dictionnaire qui permet à un seul template (`liste.html`) et à une seule série de routes de servir les trois types.**

### 5.3 La partie variable des URL

```python
ROUTE = '<any(livres,cds,dvds):type_>'
```

Cette portion d'URL n'accepte que `livres`, `cds` ou `dvds`. Le texte capturé arrive dans la fonction de route sous le nom `type_`, et sert de clé pour `TYPES[type_]`. Une adresse comme `/musique` renvoie automatiquement une erreur 404.

### 5.4 Les deux fonctions utilitaires

- **`lire_formulaire(t)`** parcourt `t['champs']`, lit chaque valeur dans `request.form`, convertit les champs numériques en entiers (ou `None`), et renvoie un dictionnaire `{nom_du_champ: valeur}`.
- **`chercher(t, q)`** construit la requête sur `t['model']`, ajoute un filtre `ilike` sur les colonnes de `t['recherche']` si `q` n'est pas vide, puis trie par titre.

### 5.5 Les routes

| URL | Méthode | Fonction | Résultat |
| --- | --- | --- | --- |
| `/` | GET | `accueil` | Affiche `index.html` |
| `/livres` | GET | `liste` | Affiche `liste.html` (recherche avec `?q=...`) |
| `/livres/ajouter` | POST | `ajouter` | Enregistre puis redirige vers la liste |
| `/livres/12/modifier` | GET et POST | `modifier` | GET : liste avec formulaire pré-rempli. POST : enregistre puis redirige |
| `/livres/12/supprimer` | POST | `supprimer` | Supprime puis redirige vers la liste |

(Remplace `livres` par `cds` ou `dvds` : c'est le même code.)

Trois détails importants :

- **`ajouter` et `supprimer` n'acceptent que POST** : on ne peut pas modifier la base par simple clic sur un lien.
- **Redirection après POST** (`redirect(url_for('liste', ...))`) : si l'utilisateur actualise la page, le navigateur ne renvoie pas le formulaire une seconde fois.
- **`element`** : `liste.html` sert aussi de page de modification. Quand `element` vaut `None`, le formulaire est en mode « ajout » ; quand il contient un objet, il est en mode « modification ».

### 5.6 La création des tables

```python
with app.app_context():
    db.create_all()
```

Au démarrage, SQLAlchemy crée les tables qui n'existent pas encore, d'après les classes de `models.py`. Il **ne modifie pas** une table déjà existante (voir la section 9).

---

## 6. Les templates (Jinja)

### 6.1 L'héritage

`base.html` est le squelette de toutes les pages. Il définit deux « trous » :

- `{% block titre %}` : le titre de l'onglet ;
- `{% block contenu %}` : le corps de la page.

`index.html` et `liste.html` commencent par `{% extends 'base.html' %}` et ne remplissent que ces deux blocs. L'en-tête, le menu et les messages flash sont donc écrits **une seule fois**.

### 6.2 Ce que fait <span style="color: dodgerblue;">base.html</span>

- Charge la police Google Fonts et le fichier CSS, avec `url_for('static', filename='css/style.css')`.
- Calcule `actif` : le type de la page en cours (`livres`, `cds`, `dvds`, ou vide sur l'accueil), à partir de `request.view_args`.
- Donne cette valeur comme **classe CSS** à la balise `<body>` (voir la section 7).
- Construit le menu avec une boucle sur `livres`, `cds` et `dvds`, et marque le lien actif avec `aria-current`.
- Affiche les messages `flash` envoyés par `app.py`.

### 6.3 Ce que fait <span style="color: dodgerblue;">liste.html</span>

Il reçoit de `app.py` les variables `type_`, `t`, `elements`, `element` et `q`.

- **Le formulaire est généré par une boucle** sur `t.champs` : pour chaque champ, le template écrit un `<textarea>`, un `<select>` ou un `<input>` selon son `type`. Aucun champ n'est écrit à la main.
- **`element|attr(c.nom)`** lit l'attribut dont le nom est dans `c.nom` (équivalent Jinja du `getattr` de Python). C'est ce qui pré-remplit le formulaire en mode modification.
- **L'adresse du formulaire change** selon le mode : `url_for('ajouter', ...)` ou `url_for('modifier', ...)`.
- **Le tableau** est généré par deux boucles : une sur `t.colonnes` pour les en-têtes, une sur `elements` pour les lignes. Le bloc `{% else %}` affiche « Rien pour l'instant » quand la liste est vide.
- **La suppression** est un petit formulaire POST avec une confirmation JavaScript.
- **La recherche** est un formulaire GET qui ajoute `?q=...` à l'URL.

### 6.4 Le lien entre templates et routes

Les noms passés à `url_for` (`accueil`, `liste`, `ajouter`, `modifier`, `supprimer`) sont les **noms des fonctions de `app.py`**. Si tu renommes une fonction de route, il faut mettre à jour tous les templates qui l'utilisent.

---

## 7. <span style="color: dodgerblue;">style.css</span> et la couleur d'accent

Chaque type a sa couleur : vert pour les livres, violet pour les CD, rouge pour les DVD. Voici la chaîne qui l'applique :

1. L'URL contient `livres`, `cds` ou `dvds` (`app.py`, paramètre `type_`).
2. `base.html` calcule `actif` et le pose comme classe sur `<body>`.
3. Le CSS contient des règles comme `body.livres { --accent: var(--livres) }`.
4. Tous les éléments qui utilisent `var(--accent)` (bordure des cartes, boutons, contour de focus) changent de couleur **sans qu'on touche au HTML**.

Sur l'accueil, `actif` est vide : `--accent` garde sa valeur par défaut (la couleur du texte).

Les liens du menu et les « dos de livres » de l'accueil utilisent directement les couleurs de chaque type, donc elles restent visibles quelle que soit la page.

---

## 8. Trois scénarios pas à pas

### A. Ajouter un CD

1. Sur `/cds`, l'utilisateur remplit le formulaire (généré par `liste.html` à partir de `TYPES['cds']['champs']`) et clique sur « Enregistrer ».
2. Le navigateur envoie `POST /cds/ajouter`.
3. `ajouter('cds')` appelle `lire_formulaire`, qui renvoie par exemple `{'titre': '...', 'artiste': '...', 'annee': 1997, ...}`.
4. Si le titre est vide : `flash('Le titre est obligatoire.', 'erreur')`. Sinon : `Cd(**valeurs)` crée l'objet, `db.session.add` puis `db.session.commit` l'écrivent dans la table `cd`, et `flash('Enregistré.')` prépare le message.
5. `redirect` renvoie le navigateur vers `/cds` : la page se recharge, `base.html` affiche le message, et le nouveau CD apparaît dans le tableau.

### B. Modifier un livre

1. Clic sur « Modifier » : `GET /livres/12/modifier`.
2. `modifier` charge le livre avec `db.get_or_404` et réaffiche `liste.html` avec `element=livre`. Le formulaire est pré-rempli et son action pointe vers `modifier`.
3. Clic sur « Enregistrer » : `POST /livres/12/modifier`. La boucle `setattr(element, nom, valeur)` met à jour chaque attribut, puis `commit` et redirection.

### C. Rechercher

Le champ de recherche envoie `GET /livres?q=zola`. `liste` lit `request.args.get('q')`, `chercher` ajoute un filtre sur `titre` **ou** `auteur` (`recherche` dans `TYPES`), et le tableau n'affiche que les résultats. S'il n'y en a aucun, le message « Aucun résultat pour… » s'affiche.

---

## 9. « Je veux changer… : que dois-je modifier ? »

| Je veux… | Fichier(s) à modifier |
| --- | --- |
| Changer le texte d'un libellé de formulaire | `app.py` : l'appel `champ(...)` concerné |
| Changer les colonnes du tableau | `app.py` : `TYPES[...]['colonnes']` uniquement |
| Changer les colonnes interrogées par la recherche | `app.py` : `TYPES[...]['recherche']` |
| Changer les couleurs | `style.css` : variables de `:root` |
| Changer l'en-tête ou le menu | `base.html` |
| Changer le texte de l'accueil | `index.html` |
| Ajouter un champ (ex. « prêté à » pour les livres) | `models.py` (colonne) + `app.py` (entrée dans `champs`, éventuellement dans `colonnes`). Aucun template à toucher. **Voir l'avertissement ci-dessous.** |
| Ajouter un type (ex. jeux vidéo) | `models.py` (nouvelle classe) ; `app.py` (import, entrée `TYPES`, ajout de `jeux` dans `ROUTE`) ; `base.html` (liste du menu) ; `index.html` (nouvelle carte) ; `style.css` (couleur `--jeux`, règles `body.jeux`, `nav a.jeux`, `.spine.jeux`) |

**Avertissement important :** `db.create_all()` crée les tables manquantes mais **n'ajoute pas de colonne** à une table existante. Après avoir ajouté un champ dans `models.py`, il faut soit ajouter la colonne à la main dans la base (`ALTER TABLE livre ADD COLUMN pret_a VARCHAR(100);`), soit supprimer `mediatheque.db` pour la recréer (en perdant les données).

---

## 10. Points d'attention

- **`SECRET_KEY`** vaut `changez-moi` : à remplacer par une vraie valeur secrète avant tout déploiement.
- **`debug=True`** ne doit pas rester activé en production.
- **`.gitignore` exclut `instance/`** : la base de données n'est donc **pas** envoyée sur GitHub. Pense à la sauvegarder séparément.
- **Consulter la base :** le README propose `sqlite3 livres.db`, mais les données sont dans `instance/mediatheque.db`. La bonne commande est `sqlite3 instance/mediatheque.db`, puis `.tables` et `SELECT * FROM livre;`.
- **Lancer l'application :** `flask --app app run --debug` (ou `python app.py`).
- **Avant un `git add .` :** les fichiers `me` et ```podman run -d ``.txt``` seraient ajoutés au dépôt. Le second contient des commandes avec un mot de passe de laboratoire : mieux vaut le sortir du dossier ou l'ajouter au `.gitignore`.

---

## 11. Pour vérifier ta compréhension

1. Que se passe-t-il si tu ouvres `/musique` ? Pourquoi ?
2. Pourquoi `ajouter` se termine-t-il par un `redirect` plutôt que par un `render_template` ?
3. Où est défini le fait que le champ « Lecture » est une liste déroulante, et quel fichier la dessine ?
4. Pourquoi les couleurs changent-elles d'une page à l'autre alors que le CSS est le même ?

**Réponses :**

1. Erreur 404 : `ROUTE` n'accepte que `livres`, `cds` et `dvds`.
2. Pour éviter qu'une actualisation de la page renvoie le formulaire une seconde fois (et crée un doublon).
3. Dans `app.py` (`champ('lecture', ..., 'select', [...])`) pour la définition ; dans `liste.html` (branche `select` de la boucle) pour le dessin.
4. Parce que `base.html` met le type courant en classe de `<body>`, et que le CSS associe à chaque classe une valeur de `--accent`.
