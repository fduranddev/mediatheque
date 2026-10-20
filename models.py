from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Livre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    auteur = db.Column(db.String(150))
    editeur = db.Column(db.String(150))
    annee = db.Column(db.Integer)
    isbn = db.Column(db.String(20))
    categorie = db.Column(db.String(100))
    etagere = db.Column(db.String(50))
    lecture = db.Column(db.String(20), default="À lire")
    notes = db.Column(db.Text)


class Cd(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    artiste = db.Column(db.String(150))
    annee = db.Column(db.Integer)
    pistes = db.Column(db.Integer)
    label = db.Column(db.String(150))
    genre = db.Column(db.String(100))
    emplacement = db.Column(db.String(50))
    notes = db.Column(db.Text)


class Dvd(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    realisateur = db.Column(db.String(150))
    annee = db.Column(db.Integer)
    duree = db.Column(db.Integer)
    genre = db.Column(db.String(100))
    emplacement = db.Column(db.String(50))
    vu = db.Column(db.String(10), default="Non")
    notes = db.Column(db.Text)
