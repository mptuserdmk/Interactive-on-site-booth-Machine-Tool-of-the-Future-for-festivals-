import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from app.config.settings import settings

class CombinationManager:
    def __init__(self, data_file: Optional[Path] = None):
        self.data_file = data_file or (settings.DATA_DIR / "combinations.json")
        self._combinations: List[Dict[str, Any]] = []
        self._index: Dict[tuple, Dict[str, Any]] = {}
        self.load()

    def load(self):
        if not self.data_file.exists():
            raise FileNotFoundError(f"Combinations file not found: {self.data_file}")
        
        with open(self.data_file, "r", encoding="utf-8") as f:
            self._combinations = json.load(f)

        self._index = {}
        for item in self._combinations:
            key = (item["element"], item["power"], item["color"])
            self._index[key] = item

    def get_all(self) -> List[Dict[str, Any]]:
        return self._combinations

    def find(self, element: str, power: str, color: str) -> Optional[Dict[str, Any]]:
        return self._index.get((element.lower(), power.lower(), color.lower()))

    def get_by_id(self, combo_id: int) -> Optional[Dict[str, Any]]:
        for item in self._combinations:
            if item.get("id") == combo_id:
                return item
        return None

combination_manager = CombinationManager()
