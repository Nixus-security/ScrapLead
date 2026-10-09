# 🐀 GnawLead — Pipeline de Scraping & Lead Enrichment

Rat de traque : scrape Reddit/Twitter, score l'intention d'achat par IA, enrichit via Apollo/Hunter, exporte CSV chaud.

## Architecture

```
src/
├── main.py              # Orchestrateur du pipeline (scrape -> IA -> enrich -> export)
├── config.py            # Config centralisée (.env)
├── config/targets.py    # Gestion des campagnes (targets.json)
├── scrapers/            # Reddit (asyncpraw), Twitter (Playwright), ProxyManager
├── ai/                  # OpenRouter: scoring d'intention + prompts + filtres
├── enricher/            # Apollo + Hunter (email/company enrichment)
├── export/              # CSV exporter + formatters/sanitisation
├── outreach/            # Email (Resend), DM (Playwright), rate limiter token bucket
└── discord_bot/         # Bot de pilotage (!generate, !addcampaign...)
```

## Setup

```bash
bash scripts/setup.sh          # venv + deps + chromium + .env
# édite .env avec tes clés API
python -m src.main --list
python -m src.main --campaign agence_marketing
```

## Docker

```bash
docker compose run --rm pipeline python -m src.main --campaign agence_marketing
docker compose up bot           # bot Discord en continu
```

## Commandes

| Commande | Description |
|---|---|
| `python -m src.main --list` | Liste les campagnes |
| `python -m src.main --campaign <nom>` | Lance le pipeline complet |
| `python -m src.discord_bot.bot` | Démarre le bot Discord |
| `pytest tests/ -v` | Tests unitaires |
| `python scripts/clear_cache.py` | Nettoie data/logs |

## Pipeline

1. **Scraping** parallèle Reddit + Twitter (delays aléatoires, proxies rotatifs).
2. **Dédoublonnage** brut avant IA (économie de tokens).
3. **Scoring IA** (OpenRouter, JSON robuste, retry exponentiel, concurrence limitée).
4. **Enrichissement** Apollo (parallèle, semaphore 5).
5. **Filtrage** seuil `AI_SCORE_THRESHOLD` + déduplication email/username.
6. **Export** CSV trié par score (`data/exports/`).

## Sécurité

- `.env` jamais commité (gitignore), cookies LinkedIn hors repo.
- Respect des ToS plateformes : utilise les API officielles quand elles existent.
- Outreach opt-in uniquement, désinscription obligatoire (CAN-SPAM/GDPR).
