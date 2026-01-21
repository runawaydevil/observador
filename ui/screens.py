import json
import time
from pathlib import Path
from textual.screen import Screen
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Static, Input, Button, ListView, ListItem, Label
from textual.binding import Binding
from rich.text import Text
from rich.panel import Panel
from rich.console import Group
from engine.rng import make_seed, SeededRNG
from engine.taboos import check_taboos
from .widgets import FooterWidget, ReadingDisplay


class StyledStatic(Static):
    def __init__(self, text: str, style: str = "", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._text = text
        self._style = style
    
    def render(self):
        return Text(self._text, style=self._style)


class HomeScreen(Screen):
    BINDINGS = [
        Binding("c", "consult", "Consultar"),
        Binding("r", "register", "Registro"),
        Binding("q", "quit", "Sair"),
    ]
    
    def compose(self):
        title = Text("OBSERVADOR", style="bold magenta")
        subtitle = Text("O Véu do Compasso", style="dim white")
        seal = Text("🜍", style="yellow")
        
        with Container():
            yield Static(Panel(Group(title, subtitle, seal), title="Oráculo Terminal", border_style="magenta"))
            yield StyledStatic("\n[C] Consultar  [R] Registro  [Q] Sair\n", style="cyan")
            yield FooterWidget()
    
    def action_consult(self):
        self.app.push_screen(ConsultScreen())
    
    def action_register(self):
        self.app.push_screen(RegisterScreen())
    
    def action_quit(self):
        self.app.exit()


class ConsultScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Voltar"),
    ]
    
    def compose(self):
        with Vertical():
            yield StyledStatic("Faça sua pergunta:", style="bold")
            yield Input(placeholder="Digite sua pergunta...", id="question_input")
            yield Button("Consultar", id="consult_btn", variant="primary")
            yield Static("", id="result_display")
            yield FooterWidget()
    
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "consult_btn":
            self.consult()
    
    def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "question_input":
            self.consult()
    
    def consult(self):
        question_input = self.query_one("#question_input", Input)
        question = question_input.value.strip()
        
        if not question:
            return
        
        result_display = self.query_one("#result_display", Static)
        result_display.update(Text("Consultando...", style="yellow"))
        
        app = self.app
        state = app.state
        lore = app.lore
        deck = app.deck
        interpreter = app.interpreter
        
        taboo, taboo_data = check_taboos(question, lore)
        
        if taboo and taboo.id == "T6":
            result_display.update(Panel(
                Text("Eu não selo portas finais.\n\nProcure ajuda agora. Se houver risco imediato, ligue para serviços de emergência locais.", style="bold red"),
                title="Interrupção",
                border_style="red"
            ))
            return
        
        if taboo:
            state.apply_taboo_penalty(taboo.debt_delta, taboo.entropy_delta)
            result_display.update(Panel(
                Text(f"{taboo.response}\n\n{taboo.alternative}", style="yellow"),
                title="Tabu Detectado",
                border_style="yellow"
            ))
            return
        
        is_repeat = state.check_repeat_question(question)
        if is_repeat:
            state.apply_repeat_penalty()
        
        if "sim ou não" in question.lower() or "certeza" in question.lower():
            state.apply_certainty_penalty()
        
        state.consult_count += 1
        state.last_questions.append(question)
        if len(state.last_questions) > 5:
            state.last_questions.pop(0)
        
        seed = make_seed(state.session_seed_base, question, state.consult_count)
        rng = SeededRNG(seed)
        
        symbols = deck.draw_three(state, rng, question)
        state.last_draw = [s.id for s in symbols]
        
        domains = []
        for symbol in symbols:
            domains.extend(symbol.dominios)
        state.update_memory([s.id for s in symbols], domains)
        
        reading_data = interpreter.interpret(state, symbols, taboo, lore, rng)
        
        state.last_answer_hash = str(hash(str(reading_data)))
        
        result_display.mount(ReadingDisplay(reading_data))
        
        storage_path = Path(__file__).parent.parent / "storage" / "readings.jsonl"
        with open(storage_path, 'a', encoding='utf-8') as f:
            record = {
                "timestamp": time.time(),
                "question": question,
                "seed": seed,
                "symbols": [s.id for s in symbols],
                "state_snapshot": state.to_dict(),
                "reading_text": {
                    "seal": reading_data["seal"],
                    "liturgy": reading_data["liturgy"],
                    "reading": reading_data["reading"],
                    "coda": reading_data["coda"]
                },
                "ato": reading_data["ato"],
                "preco": reading_data["preco"]
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    def action_back(self):
        self.app.pop_screen()


class RegisterScreen(Screen):
    BINDINGS = [
        Binding("escape", "back", "Voltar"),
    ]
    
    def compose(self):
        with Vertical():
            yield StyledStatic("Registro de Leituras", style="bold")
            yield ListView(id="readings_list")
            yield FooterWidget()
    
    def on_mount(self):
        self.load_readings()
    
    def load_readings(self):
        storage_path = Path(__file__).parent.parent / "storage" / "readings.jsonl"
        readings_list = self.query_one("#readings_list", ListView)
        
        if not storage_path.exists():
            readings_list.append(ListItem(Label("Nenhuma leitura registrada.")))
            return
        
        readings = []
        with open(storage_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    readings.append(json.loads(line))
        
        readings.reverse()
        
        for reading in readings[:20]:
            question = reading.get("question", "Sem pergunta")
            timestamp = reading.get("timestamp", 0)
            from datetime import datetime
            dt = datetime.fromtimestamp(timestamp)
            label_text = f"{dt.strftime('%Y-%m-%d %H:%M')} — {question[:50]}..."
            readings_list.append(ListItem(Label(label_text)))
    
    def action_back(self):
        self.app.pop_screen()
