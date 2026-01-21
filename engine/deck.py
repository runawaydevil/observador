import json
from typing import List, Tuple
from dataclasses import dataclass
from .rng import SeededRNG
from .state import State


@dataclass
class Symbol:
    id: str
    nome: str
    glifo: str
    glifo_fallback: str
    cor_tag: str
    dominios: List[str]
    correspondencias: dict
    polaridade: float
    raridade: int
    gatilhos: List[str]
    contraindicacoes: List[str]
    frases_nucleo: List[str]
    sinais_observaveis: List[str]
    perguntas_diagnostico: List[str]
    intervencoes_minimas: List[dict]
    excecoes: List[str]
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data["id"],
            nome=data["nome"],
            glifo=data["glifo"],
            glifo_fallback=data["glifo_fallback"],
            cor_tag=data["cor_tag"],
            dominios=data["dominios"],
            correspondencias=data["correspondencias"],
            polaridade=data["polaridade"],
            raridade=data["raridade"],
            gatilhos=data.get("gatilhos", []),
            contraindicacoes=data.get("contraindicacoes", []),
            frases_nucleo=data["frases_nucleo"],
            sinais_observaveis=data.get("sinais_observaveis", []),
            perguntas_diagnostico=data.get("perguntas_diagnostico", []),
            intervencoes_minimas=data.get("intervencoes_minimas", []),
            excecoes=data.get("excecoes", [])
        )


class Deck:
    def __init__(self, symbols: List[Symbol]):
        self.symbols = symbols
    
    @classmethod
    def load_from_json(cls, path: str):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        symbols = [Symbol.from_dict(s) for s in data["symbols"]]
        return cls(symbols)
    
    def draw_three(self, state: State, rng: SeededRNG, question: str) -> Tuple[Symbol, Symbol, Symbol]:
        question_lower = question.lower()
        weights = []
        
        echo_symbol_id = state.get_echo_symbol()
        force_echo = state.check_repeat_question(question) and state.last_draw
        
        for symbol in self.symbols:
            weight = 1.0
            
            if symbol.raridade == 5:
                weight *= 0.3
            elif symbol.raridade == 4:
                weight *= 0.6
            elif symbol.raridade == 3:
                weight *= 0.8
            
            motif_count = state.motif_counts.get(symbol.id, 0)
            if motif_count > 0:
                weight *= (1.0 + motif_count * 0.2)
            
            if echo_symbol_id == symbol.id:
                weight *= 1.5
            
            for contra in symbol.contraindicacoes:
                if contra.lower() in question_lower:
                    weight *= 0.3
            
            for gatilho in symbol.gatilhos:
                if gatilho.lower() in question_lower:
                    weight *= 1.3
            
            weights.append(max(0.1, weight))
        
        selected = []
        available = list(self.symbols)
        available_weights = list(weights)
        
        if force_echo and state.last_draw:
            echo_id = state.last_draw[0]
            echo_symbol = next((s for s in available if s.id == echo_id), None)
            if echo_symbol:
                selected.append(echo_symbol)
                idx = available.index(echo_symbol)
                available.pop(idx)
                available_weights.pop(idx)
        
        while len(selected) < 3:
            if not available:
                break
            symbol = rng.choices(available, weights=available_weights, k=1)[0]
            selected.append(symbol)
            idx = available.index(symbol)
            available.pop(idx)
            available_weights.pop(idx)
        
        if len(selected) < 3:
            while len(selected) < 3:
                symbol = rng.choice(self.symbols)
                if symbol not in selected:
                    selected.append(symbol)
        
        return tuple(selected[:3])
