from flask import Flask, flash, redirect, render_template, request, url_for
from sqlalchemy import or_

from models import Cd, Dvd, Livre, db

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mediatheque.db"
app.config["SECRET_KEY"] = "changez-moi"  # à remplacer avant tout déploiement
db.init_app(app)


def champ(nom, label, type="text", options=None, plein=False):
    return {"nom": nom, "label": label, "type": type, "options": options, "plein": plein}


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

ROUTE = "<any(livres,cds,dvds):type_>"


def lire_formulaire(t):
    valeurs = {}
    for c in t["champs"]:
        v = request.form.get(c["nom"], "").strip()
        if c["type"] == "number":
            valeurs[c["nom"]] = int(v) if v.isdigit() else None
        else:
            valeurs[c["nom"]] = v
    return valeurs


def chercher(t, q):
    modele = t["model"]
    requete = modele.query
    if q:
        requete = requete.filter(or_(*[getattr(modele, n).ilike(f"%{q}%") for n in t["recherche"]]))
    return requete.order_by(modele.titre).all()


@app.route("/")
def accueil():
    return render_template("index.html")


@app.route(f"/{ROUTE}")
def liste(type_):
    t = TYPES[type_]
    q = request.args.get("q", "").strip()
    return render_template("liste.html", type_=type_, t=t, elements=chercher(t, q), element=None, q=q)


@app.post(f"/{ROUTE}/ajouter")
def ajouter(type_):
    t = TYPES[type_]
    valeurs = lire_formulaire(t)
    if not valeurs["titre"]:
        flash("Le titre est obligatoire.", "erreur")
    else:
        db.session.add(t["model"](**valeurs))
        db.session.commit()
        flash("Enregistré.")
    return redirect(url_for("liste", type_=type_))


@app.route(f"/{ROUTE}/<int:id>/modifier", methods=["GET", "POST"])
def modifier(type_, id):
    t = TYPES[type_]
    element = db.get_or_404(t["model"], id)
    if request.method == "POST":
        valeurs = lire_formulaire(t)
        if not valeurs["titre"]:
            flash("Le titre est obligatoire.", "erreur")
        else:
            for nom, valeur in valeurs.items():
                setattr(element, nom, valeur)
            db.session.commit()
            flash("Enregistré.")
            return redirect(url_for("liste", type_=type_))
    return render_template("liste.html", type_=type_, t=t, elements=chercher(t, ""), element=element, q="")


@app.post(f"/{ROUTE}/<int:id>/supprimer")
def supprimer(type_, id):
    element = db.get_or_404(TYPES[type_]["model"], id)
    db.session.delete(element)
    db.session.commit()
    flash("Supprimé.")
    return redirect(url_for("liste", type_=type_))


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
