import os
import psycopg2
from flask import Flask, jsonify, request

app = Flask(__name__)
DB_URL = os.environ["DATABASE_URL"]


def get_conn():
    return psycopg2.connect(DB_URL)


def init_db():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cours (
                id SERIAL PRIMARY KEY,
                nom TEXT NOT NULL,
                professeur TEXT NOT NULL
            )
        """)


@app.get("/health")
def health():
    return {"status": "ok", "service": "cours"}


@app.get("/cours")
def lister():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, nom, professeur FROM cours ORDER BY id")
        rows = cur.fetchall()
    return jsonify([{"id": r[0], "nom": r[1], "professeur": r[2]} for r in rows])


@app.get("/cours/<int:id>")
def detail(id):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, nom, professeur FROM cours WHERE id = %s", (id,))
        r = cur.fetchone()
    if r is None:
        return {"erreur": "cours introuvable"}, 404
    return {"id": r[0], "nom": r[1], "professeur": r[2]}


@app.post("/cours")
def ajouter():
    data = request.get_json()
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO cours (nom, professeur) VALUES (%s, %s) RETURNING id",
            (data["nom"], data["professeur"]),
        )
        new_id = cur.fetchone()[0]
    return {"id": new_id, "nom": data["nom"], "professeur": data["professeur"]}, 201


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
