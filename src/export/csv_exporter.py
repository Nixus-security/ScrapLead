import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List
from src.config import Config

class CSVExporter:
    def __init__(self):
        self.columns = [
            'platform', 'username', 'first_name', 'last_name', 'email',
            'company', 'title', 'ai_score', 'ai_reason', 'text',
            'source_url', 'scraped_at'
        ]
    
    def export(self, leads: list[dict]) -> Path:
        df = pd.DataFrame(leads)
        
        for col in self.columns:
            if col not in df.columns:
                df[col] = ''
        
        df = df[self.columns]
        df = df.sort_values('ai_score', ascending=False)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"gnawlead_hot_{timestamp}.csv"
        filepath = Config.EXPORTS_DIR / filename
        
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        return filepath