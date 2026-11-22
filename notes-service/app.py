import os
import psycopg2
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)
DB_URL = os.environ["DATABASE_URL"]

# Adresses des autres microservices : on utilise leur NOM dans le reseau Docker
ETUDIANTS_URL = os.environ["ETUDIANTS_URL"]   # http://etudiants:5000
COURS_URL = os.environ["COURS_URL"]           # http://cours:5000


def get_conn():
    return psycopg2.connect(DB_URL)


def init_db():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id SERIAL PRIMARY KEY,
                etudiant_id INTEGER NOT NULL,
                cours_id INTEGER NOT NULL,
                valeur REAL NOT NULL
            )
        """)


def appeler(url):
    """Appelle un autre microservice.
    Renvoie (donnees, None) si OK, ou (None, message_erreur) sinon."""
    try:
        r = requests.get(url, timeout=3)
    except requests.exceptions.RequestException:
        return None, "service indisponible"
    if r.status_code == 404:
        return None, "introuvable"
    return r.json(), None


@app.get("/health")
def health():
    return {"status": "ok", "service": "notes"}


@app.post("/notes")
def ajouter():
    data = request.get_json()
    etudiant_id = data["etudiant_id"]
    cours_id = data["cours_id"]
    valeur = data["valeur"]

    # 1) On demande au service ETUDIANTS si l'etudiant existe
    etudiant, err = appeler(f"{ETUDIANTS_URL}/etudiants/{etudiant_id}")
    if err:
        return {"erreur": f"etudiant : {err}"}, 404 if err == "introuvable" else 503

    # 2) On demande au service COURS si le cours existe
    cours, err = appeler(f"{COURS_URL}/cours/{cours_id}")
    if err:
        return {"erreur": f"cours : {err}"}, 404 if err == "introuvable" else 503

    # 3) Tout est OK : on enregistre la note dans NOTRE base
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO notes (etudiant_id, cours_id, valeur) VALUES (%s, %s, %s) RETURNING id",
            (etudiant_id, cours_id, valeur),
        )
        new_id = cur.fetchone()[0]

    return {"id": new_id, "etudiant": etudiant["nom"], "cours": cours["nom"], "valeur": valeur}, 201


@app.get("/notes")
def lister():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, etudiant_id, cours_id, valeur FROM notes ORDER BY id")
        rows = cur.fetchall()

    resultat = []
    for note_id, etudiant_id, cours_id, valeur in rows:
        etudiant, _ = appeler(f"{ETUDIANTS_URL}/etudiants/{etudiant_id}")
        cours, _ = appeler(f"{COURS_URL}/cours/{cours_id}")
        resultat.append({
            "id": note_id,
            # si un service est en panne, on affiche quand meme la note
            "etudiant": etudiant["nom"] if etudiant else "(indisponible)",
            "cours": cours["nom"] if cours else "(indisponible)",
            "valeur": valeur,
        })
    return jsonify(resultat)


@app.get("/notes/etudiant/<int:etudiant_id>/moyenne")
def moyenne(etudiant_id):
    etudiant, err = appeler(f"{ETUDIANTS_URL}/etudiants/{etudiant_id}")
    if err:
        return {"erreur": f"etudiant : {err}"}, 404 if err == "introuvable" else 503

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT AVG(valeur), COUNT(*) FROM notes WHERE etudiant_id = %s", (etudiant_id,))
        moy, nb = cur.fetchone()

    return {
        "etudiant": etudiant["nom"],
        "nombre_de_notes": nb,
        "moyenne": round(moy, 2) if moy is not None else None,
    }


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
