# ensak-microservices-docker

Mini-projet Cloud — ENSA Kénitra
**Conception et déploiement d'une architecture microservices avec Docker**

Application de gestion des étudiants découpée en 3 microservices indépendants, chacun avec sa propre base de données, derrière une API Gateway Nginx. L'ensemble est orchestré avec Docker Compose.

## Architecture

```
                    Navigateur
                        │
                 localhost:8080
                        │
              ┌─────────▼─────────┐
              │  Gateway (Nginx)  │  frontend + routage
              └──┬──────┬──────┬──┘
                 │      │      │
        ┌────────▼┐ ┌───▼────┐ ┌▼────────┐
        │etudiants│ │ cours  │ │  notes  │──► appelle etudiants et cours (HTTP)
        └────┬────┘ └───┬────┘ └────┬────┘
             │          │           │
        ┌────▼────┐ ┌───▼────┐ ┌────▼────┐
        │PostgreSQL│ │PostgreSQL│ │PostgreSQL│   une base par service
        └─────────┘ └────────┘ └─────────┘
```

| Service | Rôle | Port (debug) |
|---|---|---|
| `gateway` | Nginx : sert l'interface web et route les requêtes | **8080** |
| `etudiants` | CRUD des étudiants (Flask) | 5001 |
| `cours` | CRUD des cours (Flask) | 5002 |
| `notes` | Notes et moyennes — vérifie l'étudiant et le cours auprès des 2 autres services | 5003 |
| `*-db` | PostgreSQL 16, une instance par service, non exposée hors du réseau Docker | — |

## Lancer le projet

Prérequis : Docker Desktop.

```bash
docker compose up -d --build
```

Interface : http://localhost:8080

Arrêter : `docker compose down` (les données sont conservées dans les volumes).

## API (via la gateway)

| Méthode | Route | Description |
|---|---|---|
| GET | `/etudiants` | Liste des étudiants |
| GET | `/etudiants/<id>` | Un étudiant |
| POST | `/etudiants` | `{"nom": "...", "filiere": "..."}` |
| GET | `/cours` | Liste des cours |
| GET | `/cours/<id>` | Un cours |
| POST | `/cours` | `{"nom": "...", "professeur": "..."}` |
| GET | `/notes` | Notes avec noms de l'étudiant et du cours |
| POST | `/notes` | `{"etudiant_id": 1, "cours_id": 1, "valeur": 16}` |
| GET | `/notes/etudiant/<id>/moyenne` | Moyenne d'un étudiant |
| GET | `/health` | État de la gateway |

## Concepts Docker mis en œuvre

- **Dockerfile** par microservice (image `python:3.12-slim`)
- **Docker Compose** : 7 conteneurs lancés avec une seule commande
- **Réseau Docker** : les services communiquent par leur nom (`http://etudiants:5000`)
- **Database per service** : 3 bases PostgreSQL indépendantes
- **Volumes** : persistance des données après redémarrage
- **Healthchecks + `depends_on`** : chaque service attend que sa base soit prête
- **API Gateway** : point d'entrée unique (Nginx)

## Démo : isolation des pannes

```bash
docker compose stop cours    # la carte "cours" passe au rouge dans l'interface
                             # étudiants fonctionne toujours, les notes affichent "(indisponible)"
docker compose start cours   # tout revient à la normale
```

## Structure

```
.
├── docker-compose.yml
├── gateway/nginx.conf
├── frontend/index.html
├── etudiants-service/   app.py · Dockerfile · requirements.txt
├── cours-service/       app.py · Dockerfile · requirements.txt
└── notes-service/       app.py · Dockerfile · requirements.txt
```
