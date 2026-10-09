import json
import logging
from pathlib import Path
from src.config import Config

logger = logging.getLogger(__name__)

class TargetManager:
    def __init__(self):
        self.targets_file = Config.BASE_DIR / "targets.json"
        self.targets = self._load_targets()
    
    def _load_targets(self) -> dict:
        if not self.targets_file.exists():
            logger.warning("targets.json introuvable. Création d'un fichier vide.")
            self._save_targets({"campaigns": {}, "default_campaign": ""})
            return {"campaigns": {}, "default_campaign": ""}
        
        with open(self.targets_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_targets(self, data: dict):
        with open(self.targets_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_campaign(self, campaign_name: str = None) -> dict:
        name = campaign_name or self.targets.get('default_campaign')
        campaign = self.targets.get('campaigns', {}).get(name)
        
        if not campaign:
            logger.error(f"Campagne introuvable: {name}")
            return None
        
        if not campaign.get('active', False):
            logger.warning(f"Campagne inactive: {name}")
            return None
        
        return campaign
    
    def list_campaigns(self) -> list[str]:
        return list(self.targets.get('campaigns', {}).keys())
    
    def add_campaign(self, name: str, keywords: list[str], platforms: list[str], limit: int = 50):
        self.targets['campaigns'][name] = {
            'keywords': keywords,
            'platforms': platforms,
            'limit': limit,
            'active': True
        }
        self._save_targets(self.targets)
        logger.info(f"Campagne ajoutée: {name}")
    
    def toggle_campaign(self, name: str):
        if name in self.targets['campaigns']:
            current = self.targets['campaigns'][name].get('active', False)
            self.targets['campaigns'][name]['active'] = not current
            self._save_targets(self.targets)
            logger.info(f"Campagne {name} {'activée' if not current else 'désactivée'}")