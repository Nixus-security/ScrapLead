import json
import logging
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from src.config import Config
from src.export.formatters import DataFormatter

logger = logging.getLogger(__name__)

def migrate_old_leads(old_file_path: str):
    old_path = Path(old_file_path)
    if not old_path.exists():
        logger.error(f"Fichier introuvable: {old_path}")
        return
    
    logger.info(f"Migration des données depuis: {old_path}")
    
    with open(old_path, 'r', encoding='utf-8') as f:
        old_data = json.load(f)
    
    migrated_leads = []
    formatter = DataFormatter()
    
    for item in old_data:
        # Mapper les anciens champs vers le nouveau schéma
        lead = {
            'platform': item.get('source', 'unknown'),
            'username': item.get('user', item.get('username', 'unknown')),
            'text': item.get('content', item.get('text', '')),
            'source_url': item.get('url', ''),
            'ai_score': item.get('score', 0),
            'email': item.get('email_address', '')
        }
        
        # Appliquer le formatage propre
        clean_lead = formatter.sanitize_lead(lead)
        migrated_leads.append(clean_lead)
    
    # Sauvegarder dans le nouveau format
    new_file = Config.RAW_LEADS_DIR / f"migrated_{old_path.name}"
    with open(new_file, 'w', encoding='utf-8') as f:
        json.dump(migrated_leads, f, ensure_ascii=False, indent=2)
        
    logger.info(f"✅ Migration terminée. {len(migrated_leads)} leads convertis vers: {new_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python migrate_data.py <chemin_vers_ancien_fichier.json>")
    else:
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        migrate_old_leads(sys.argv[1])