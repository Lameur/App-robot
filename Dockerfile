# Étape de construction
 FROM python:3.12-alpine AS builder

 # Installation de UV
 COPY --from=ghcr.io/astral-sh/uv /uv /bin/

 # Définition du répertoire de travail
 WORKDIR /app

 # Copie des fichiers de configuration
 COPY pyproject.toml .

 # Installation des dépendances avec UV
 RUN python -m venv .venv --copies
 RUN uv sync --no-editable --link-mode=copy --no-dev

 # Étape finale
 FROM python:3.12-alpine

 WORKDIR /app

 # Copie de UV et des dépendances depuis l'étape builder
 COPY --from=ghcr.io/astral-sh/uv /uv /bin/
 COPY --from=builder /app/.venv /app/.venv

 # Ajout du chemin des dépendances installées par UV
 ENV PATH="/app/.venv/bin:$PATH"

 # Copie du code source
 COPY src/ .

 # Commande pour exécuter le bot avec UV
 CMD ["uv", "run", "app"]
