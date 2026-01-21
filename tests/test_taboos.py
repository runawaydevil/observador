import unittest
from pathlib import Path
import sys
import json
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.taboos import check_taboos


class TestTaboos(unittest.TestCase):
    def setUp(self):
        lore_path = Path(__file__).parent.parent / "data" / "lore.json"
        with open(lore_path, 'r', encoding='utf-8') as f:
            self.lore = json.load(f)
    
    def test_taboo_detection(self):
        taboo, _ = check_taboos("Quero ganhar na loteria", self.lore)
        self.assertIsNotNone(taboo)
        self.assertEqual(taboo.id, "T1")
        
        taboo, _ = check_taboos("Preciso de diagnóstico médico", self.lore)
        self.assertIsNotNone(taboo)
        self.assertEqual(taboo.id, "T2")
        
        taboo, _ = check_taboos("Como hackear um sistema", self.lore)
        self.assertIsNotNone(taboo)
        self.assertEqual(taboo.id, "T3")
    
    def test_taboo_response(self):
        taboo, _ = check_taboos("Quero ganhar na loteria", self.lore)
        self.assertIsNotNone(taboo)
        self.assertGreater(taboo.debt_delta, 0)
        self.assertIn("números", taboo.response.lower())


if __name__ == '__main__':
    unittest.main()
