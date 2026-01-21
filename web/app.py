from flask import Flask
from pathlib import Path
import json
from engine.state import State
from engine.deck import Deck
from engine.interpret import Interpreter


def create_app():
    web_path = Path(__file__).parent
    app = Flask(__name__, 
                template_folder=str(web_path / 'templates'),
                static_folder=str(web_path / 'static'))
    app.secret_key = 'observador-secret-key-change-in-production'
    
    base_path = web_path.parent
    data_path = base_path / "data"
    
    lore_path = data_path / "lore.json"
    deck_path = data_path / "deck.json"
    templates_path = data_path / "templates.json"
    
    with open(lore_path, 'r', encoding='utf-8') as f:
        lore = json.load(f)
    
    deck = Deck.load_from_json(str(deck_path))
    interpreter = Interpreter(str(templates_path), deck=deck)
    
    app.config['LORE'] = lore
    app.config['DECK'] = deck
    app.config['INTERPRETER'] = interpreter
    app.config['BASE_PATH'] = base_path
    
    from . import routes
    app.register_blueprint(routes.bp)
    
    return app
