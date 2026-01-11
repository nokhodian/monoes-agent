import os
import json
import logging
from datetime import datetime
from typing import Any, List

logger = logging.getLogger(__name__)

class FileStorage:
    # src/data/results
    RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'results')

    @staticmethod
    def ensure_directory():
        if not os.path.exists(FileStorage.RESULTS_DIR):
            os.makedirs(FileStorage.RESULTS_DIR)

    @staticmethod
    def save(data: List[Any], action_name: str = "unknown") -> bool:
        """
        Save data to a JSON file.
        
        Args:
            data: List of data items to save
            action_name: Name of the action for the filename
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            FileStorage.ensure_directory()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Sanitize filename
            safe_name = "".join([c for c in action_name if c.isalpha() or c.isdigit() or c==' ' or c=='_']).rstrip()
            safe_name = safe_name.replace(' ', '_')
            
            filename = f"{safe_name}_{timestamp}.json"
            filepath = os.path.join(FileStorage.RESULTS_DIR, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"✅ Saved {len(data)} items to file: {filepath}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save to file: {e}")
            return False
