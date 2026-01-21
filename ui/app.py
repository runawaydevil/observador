import json
import os
from pathlib import Path
from textual.app import App
from .screens import HomeScreen
from engine.state import State
from engine.deck import Deck
from engine.interpret import Interpreter


class OracleApp(App):
    CSS = """
    Screen {
        background: $surface;
    }
    """
    
    TITLE = "OBSERVADOR"
    
    def __init__(self):
        super().__init__()
        self.state = State()
        self.lore = {}
        self.deck = None
        self.interpreter = None
        self.data_path = Path(__file__).parent.parent / "data"
        self.storage_path = Path(__file__).parent.parent / "storage"
    
    def on_mount(self) -> None:
        self.load_data()
        self.push_screen(HomeScreen())
    
    def load_data(self):
        lore_path = self.data_path / "lore.json"
        deck_path = self.data_path / "deck.json"
        templates_path = self.data_path / "templates.json"
        
        with open(lore_path, 'r', encoding='utf-8') as f:
            self.lore = json.load(f)
        
        self.deck = Deck.load_from_json(str(deck_path))
        self.interpreter = Interpreter(str(templates_path))