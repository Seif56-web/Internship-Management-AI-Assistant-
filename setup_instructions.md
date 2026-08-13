# Gestion des Stagiaires - Hutchinson

## Prérequis

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+

## Installation

### 1. Base de données

```bash
# Créer la base PostgreSQL
psql -U postgres -c "CREATE DATABASE gestion_stagiaires;"
```

### 2. Backend

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
# source venv/bin/activate

pip install -r requirements.txt
```

### 3. Frontend

```bash
cd frontend
npm install
```

## Lancement

### 1. Backend

```bash
cd backend
# Activer l'environnement virtuel d'abord
uvicorn app.main:app --reload --port 8000
```

### 2. Seed (première fois seulement)

```bash
cd backend
python seed.py
```

### 3. Frontend

```bash
cd frontend
npm run dev
```

L'application est accessible sur http://localhost:5173

## Comptes de démo

| Rôle | Email | Mot de passe |
|------|-------|-------------|
| RH | rh@hutchinson.tn | admin123 |
| Encadrant | encadrant@hutchinson.tn | admin123 |
| Admin | admin@hutchinson.tn | admin123 |

## Architecture

```
backend/
  app/
    main.py          # Point d'entrée FastAPI
    config.py        # Configuration
    database.py      # Connexion PostgreSQL
    models/          # Modèles SQLAlchemy
    schemas/         # Schémas Pydantic
    auth/            # Authentification JWT
    services/        # Logique métier
    routers/         # Points d'API
    utils/           # Utilitaires (PDF)
  seed.py            # Script d'initialisation

frontend/
  src/
    components/      # Composants réutilisables
    pages/           # Pages de l'application
    services/        # Appels API
    hooks/           # Hooks personnalisés
    context/         # Contexte React (auth)
```
