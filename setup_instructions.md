# Gestion des Stagiaires - Hutchinson

## Prérequis

- Python 3.10+ (testé en 3.12)
- Node.js 18+
- Ollama (LLM local, aucune clé API nécessaire) — https://ollama.com
- Aucune base de données externe n'est requise : le projet utilise **SQLite**
  (fichier `backend/gestion_stagiaires.db`).

## 1. Ollama (chatbot local)

```bash
# Installer Ollama (voir https://ollama.com/download), puis :
ollama pull qwen3:8b
ollama serve
```

Ollama doit tourner sur `http://127.0.0.1:11434` (valeur par défaut). Le
backend s'y connecte via une API compatible OpenAI, sans clé API
(`LLM_API_KEY` reste vide dans `.env`).

## 2. Backend

```bash
cd backend
python -m venv .venv

# Windows :
.venv\Scripts\activate
# Linux/Mac :
# source .venv/bin/activate

pip install -r requirements.txt
```

> Note (Windows, optionnel) : `sentence-transformers` installe `torch` comme
> dépendance. Si vous n'avez pas de GPU et voulez éviter un téléchargement
> volumineux, installez d'abord la version CPU :
> `pip install torch --index-url https://download.pytorch.org/whl/cpu`
> puis relancez `pip install -r requirements.txt`.

Copiez `.env.example` en `.env` (les valeurs par défaut fonctionnent telles
quelles en local) :

```bash
# Windows : copy .env.example .env
# Linux/Mac : cp .env.example .env
```

## 3. Frontend

```bash
cd frontend
npm install
```

## Lancement

### 1. Backend (toujours depuis le dossier `backend/`)

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Les chemins RAG (`RAG_VECTOR_DB_PATH`, `RAG_DOCUMENT_PATHS`) sont relatifs à
ce dossier — ne lancez pas `uvicorn` depuis la racine du projet.

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

## RAG (recherche documentaire)

Un index FAISS est déjà fourni dans `backend/rag_chroma_db/`
(`faiss_index.bin`, `faiss_metadata.json`, `faiss_chunks.pkl`) et contient
déjà les documents indexés (~3857 chunks) : au premier démarrage, **aucune
réindexation n'est nécessaire**.

Si vous ajoutez de nouveaux documents (rapports, attestations, conventions)
et voulez les indexer :

```bash
cd backend
python -m app.rag.ingestion
```

(voir `app/rag/ingestion.py` pour les options disponibles). Le module RAG
est conçu pour se dégrader proprement si `sentence-transformers` ou
`faiss-cpu` sont absents ou si l'index est manquant : le chatbot continue
alors de répondre normalement aux questions sur les données de la
plateforme (stagiaires, notes, attestations...), avec un message indiquant
que la recherche documentaire est momentanément indisponible.

## Vérification du chatbot

Une fois backend + frontend + Ollama lancés, ouvrez l'application,
connectez-vous, et testez dans le chat :

- Une question sur les données : « Combien de stagiaires sont enregistrés ? »
- Une question documentaire : « Que dit le document concernant les rapports
  de stage ? »
- Une question générale : « Bonjour, présente-toi en une phrase. »

## Tests

```bash
cd backend
pytest
# ou, plus verbeux :
pytest -q
```
