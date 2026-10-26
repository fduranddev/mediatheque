"""
Application Flask de gestion d'une médiathèque personnelle :
livres, CD audio et DVD.

Le même code gère les trois types de documents grâce au dictionnaire TYPES
(plus bas) : une seule série de routes (liste, ajout, modification,
suppression) sert pour les livres, les CD et les DVD.
"""

# --- Imports ---------------------------------------------------------------
# flash    : messages temporaires affichés à l'utilisateur ("Enregistré.")
# redirect : redirige le navigateur vers une autre URL
# render_template : génère une page HTML à partir d'un fichier de templates/
# request  : accès aux données envoyées par le navigateur (formulaires, ?q=...)
# url_for  : construit une URL à partir du nom d'une fonction de route
from flask import Flask, flash, redirect, render_template, request, url_for

# or_ permet de combiner plusieurs conditions avec un OU dans une requête SQL
from sqlalchemy import or_

# Les modèles (tables) et l'objet db sont définis dans models.py
from models import Cd, Dvd, Livre, db

# --- Configuration de l'application ---------------------------------------
app = Flask(__name__)

# Base SQLite : le fichier mediatheque.db est créé dans le dossier "instance/"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mediatheque.db"

# Clé secrète nécessaire à flash() (les messages passent par la session)
app.config["SECRET_KEY"] = "changez-moi"  # à remplacer avant tout déploiement

# Relie l'objet db (créé dans models.py) à cette application
db.init_app(app)


def champ(nom, label, type="text", options=None, plein=False):
    """Décrit un champ de formulaire sous forme de dictionnaire.

    nom     : nom de la colonne dans la base (et du champ dans le formulaire)
    label   : texte affiché à l'utilisateur
    type    : "text", "number", "select" ou "textarea"
    options : liste des choix possibles (pour le type "select")
    plein   : True si le champ doit occuper toute la largeur dans le formulaire
    """
    return {"nom": nom, "label": label, "type": type, "options": options, "plein": plein}


# --- Description des trois types de documents -----------------------------
# Chaque entrée contient tout ce qu'il faut pour gérer un type :
#   model     : la classe SQLAlchemy correspondante (table)
#   nom       : nom affiché au pluriel (menu, titres)
#   page      : titre de la page de liste
#   un        : forme utilisée dans les textes ("Ajouter un livre")
#   recherche : colonnes interrogées par la barre de recherche
#   champs    : champs du formulaire d'ajout / de modification
#   colonnes  : colonnes affichées dans le tableau (colonne, titre d'en-tête)
TYPES = {
    "livres": {
        "model": Livre, "nom": "Livres", "page": "Mes livres", "un": "un livre",
        "recherche": ["titre", "auteur"],
        "champs": [
            champ("titre", "Titre", plein=True), champ("auteur", "Auteur", plein=True),
            champ("editeur", "Éditeur", plein=True), champ("annee", "Année", "number"),
            champ("isbn", "ISBN"), champ("categorie", "Catégorie"), champ("etagere", "Étagère"),
            champ("lecture", "Lecture", "select", ["À lire", "En cours", "Lu"], True),
            champ("notes", "Notes", "textarea", plein=True),
        ],
        "colonnes": [("titre", "Titre"), ("auteur", "Auteur"), ("annee", "Année"),
                     ("etagere", "Étagère"), ("lecture", "Lecture")],
    },
    "cds": {
        "model": Cd, "nom": "CD", "page": "Mes CD", "un": "un CD",
        "recherche": ["titre", "artiste"],
        "champs": [
            champ("titre", "Album", plein=True), champ("artiste", "Artiste", plein=True),
            champ("annee", "Année", "number"), champ("pistes", "Pistes", "number"),
            champ("label", "Label", plein=True), champ("genre", "Genre"),
            champ("emplacement", "Emplacement"), champ("notes", "Notes", "textarea", plein=True),
        ],
        "colonnes": [("titre", "Album"), ("artiste", "Artiste"), ("annee", "Année"),
                     ("genre", "Genre"), ("emplacement", "Emplacement")],
    },
    "dvds": {
        "model": Dvd, "nom": "DVD", "page": "Mes DVD", "un": "un DVD",
        "recherche": ["titre", "realisateur"],
        "champs": [
            champ("titre", "Titre", plein=True), champ("realisateur", "Réalisateur", plein=True),
            champ("annee", "Année", "number"), champ("duree", "Durée (min)", "number"),
            champ("genre", "Genre"), champ("emplacement", "Emplacement"),
            champ("vu", "Déjà vu", "select", ["Non", "Oui"], True),
            champ("notes", "Notes", "textarea", plein=True),
        ],
        "colonnes": [("titre", "Titre"), ("realisateur", "Réalisateur"), ("annee", "Année"),
                     ("duree", "Durée"), ("vu", "Vu")],
    },
}

# Partie variable des URL : n'accepte que "livres", "cds" ou "dvds".
# Toute autre valeur (/musique, par exemple) renvoie automatiquement une 404.
# Le texte capturé est transmis aux fonctions de route dans le paramètre type_.
ROUTE = "<any(livres,cds,dvds):type_>"


def lire_formulaire(t):
    """Lit les données du formulaire envoyé et renvoie un dictionnaire
    {nom_du_champ: valeur}, prêt à être utilisé pour créer ou modifier une ligne.
    """
    valeurs = {}
    for c in t["champs"]:
        # .strip() retire les espaces au début et à la fin
        v = request.form.get(c["nom"], "").strip()
        if c["type"] == "number":
            # Champ numérique : entier si la saisie ne contient que des chiffres,
            # sinon None (la colonne reste vide en base)
            valeurs[c["nom"]] = int(v) if v.isdigit() else None
        else:
            valeurs[c["nom"]] = v
    return valeurs


def chercher(t, q):
    """Renvoie les éléments du type t, triés par titre.

    Si q n'est pas vide, ne garde que ceux dont l'une des colonnes de
    recherche (titre, auteur, artiste...) contient q, sans tenir compte
    de la casse.
    """
    modele = t["model"]
    requete = modele.query
    if q:
        # ilike = LIKE insensible à la casse ; %q% = "contient q".
        # or_ : il suffit qu'une des colonnes corresponde.
        requete = requete.filter(or_(*[getattr(modele, n).ilike(f"%{q}%") for n in t["recherche"]]))
    return requete.order_by(modele.titre).all()


# --- Routes ----------------------------------------------------------------
@app.route("/")
def accueil():
    """Page d'accueil."""
    return render_template("index.html")


@app.route(f"/{ROUTE}")
def liste(type_):
    """Affiche la liste d'un type (ex. /livres), avec recherche optionnelle (?q=...)."""
    t = TYPES[type_]
    q = request.args.get("q", "").strip()
    # element=None : le formulaire est en mode "ajout" (et non "modification")
    return render_template("liste.html", type_=type_, t=t, elements=chercher(t, q), element=None, q=q)


@app.post(f"/{ROUTE}/ajouter")
def ajouter(type_):
    """Ajoute un élément à partir du formulaire (requête POST uniquement)."""
    t = TYPES[type_]
    valeurs = lire_formulaire(t)
    if not valeurs["titre"]:
        # Le titre est la seule donnée obligatoire
        flash("Le titre est obligatoire.", "erreur")
    else:
        # t["model"](**valeurs) équivaut à Livre(titre=..., auteur=..., ...)
        db.session.add(t["model"](**valeurs))
        db.session.commit()
        flash("Enregistré.")
    # Redirection après POST : évite le double envoi si on actualise la page
    return redirect(url_for("liste", type_=type_))


@app.route(f"/{ROUTE}/<int:id>/modifier", methods=["GET", "POST"])
def modifier(type_, id):
    """Modifie un élément.

    GET  : affiche la liste avec le formulaire pré-rempli par l'élément.
    POST : enregistre les modifications.
    """
    t = TYPES[type_]
    # Renvoie une erreur 404 si l'identifiant n'existe pas
    element = db.get_or_404(t["model"], id)
    if request.method == "POST":
        valeurs = lire_formulaire(t)
        if not valeurs["titre"]:
            flash("Le titre est obligatoire.", "erreur")
        else:
            # Met à jour chaque attribut de l'objet avec la nouvelle valeur
            for nom, valeur in valeurs.items():
                setattr(element, nom, valeur)
            db.session.commit()
            flash("Enregistré.")
            return redirect(url_for("liste", type_=type_))
    # En GET (ou si le titre est vide) : on réaffiche la page avec l'élément
    # en cours de modification
    return render_template("liste.html", type_=type_, t=t, elements=chercher(t, ""), element=element, q="")


@app.post(f"/{ROUTE}/<int:id>/supprimer")
def supprimer(type_, id):
    """Supprime un élément (POST uniquement, pour éviter une suppression
    accidentelle par simple clic sur un lien)."""
    element = db.get_or_404(TYPES[type_]["model"], id)
    db.session.delete(element)
    db.session.commit()
    flash("Supprimé.")
    return redirect(url_for("liste", type_=type_))


# --- Création des tables ---------------------------------------------------
# Crée les tables manquantes au démarrage (sans toucher à celles qui existent).
# L'application doit être "active" (app_context) pour accéder à la base.
with app.app_context():
    db.create_all()

# Lancement du serveur de développement avec `python app.py`.
# debug=True : rechargement automatique et page d'erreur détaillée
# (à désactiver en production).
if __name__ == "__main__":
    app.run(debug=True)
