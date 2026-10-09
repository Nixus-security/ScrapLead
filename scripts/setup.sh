#!/usr/bin/env bash
# GnawLead - Setup rapide
set -euo pipefail

cd "$(dirname "$0")/.."

echo "🐀 [1/4] Création du venv..."
python3 -m venv .venv
source .venv/bin/activate

echo "🐀 [2/4] Installation des dépendances..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
pip install pytest pytest-asyncio aioresponses -q

echo "🐀 [3/4] Installation Chromium (Playwright)..."
playwright install chromium

echo "🐀 [4/4] Configuration..."
if [ ! -f .env ]; then
  cp .env.example .env
  echo "⚠️  .env créé depuis .env.example -> REMPLIS TES CLES API."
fi

mkdir -p data/raw_leads data/enriched_leads data/exports logs

echo "✅ Nid prêt. Active le venv: source .venv/bin/activate"
echo "   Lance une campagne: python -m src.main --campaign agence_marketing"