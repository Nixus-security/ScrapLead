import shutil
import logging
from pathlib import Path
import sys

# Ajouter le dossier parent au path pour importer config
sys.path.append(str(Path(__file__).parent.parent))
from src.config import Config

def clear_all():
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logger = logging.getLogger(__name__)
    
    targets = [
        Config.RAW_LEADS_DIR,
        Config.ENRICHED_LEADS_DIR,
        Config.EXPORTS_DIR,
        Config.LOGS_DIR,
        Path.home() / ".cache" / "ms-playwright" # Cache navigateur
    ]
    
    logger.info("🐀 Nettoyage du nid en cours...")
    for target in targets:
        if target.exists():
            try:
                shutil.rmtree(target)
                logger.info(f"✅ Supprimé: {target}")
            except Exception as e:
                logger.error(f"❌ Échec suppression {target}: {e}")
        else:
            logger.info(f"⏭️  Introuvable: {target}")
            
    # Recréer les dossiers vides
    Config.ensure_dirs()
    logger.info("✨ Nid nettoyé et prêt pour une nouvelle traque.")

if __name__ == "__main__":
    confirm = input("⚠️  Cette action supprimera TOUTES les données et logs. Continuer ? (y/N): ")
    if confirm.lower() == 'y':
        clear_all()
    else:
        print("Annulé.")