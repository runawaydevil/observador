from typing import Dict, List, Set, Tuple
from .deck import Symbol
from .rng import SeededRNG


class Lexicalizer:
    def __init__(self):
        self.domain_lexicon = {
            "voto": {
                "verbos": ["prometer", "comprometer", "selar", "jurar"],
                "qualidades": ["fidelidade", "compromisso", "juramento", "palavra"],
                "sombras": ["traição", "quebra", "infidelidade", "mentira"]
            },
            "ferro": {
                "verbos": ["limitar", "cortar", "definir", "marcar"],
                "qualidades": ["resistência", "fronteira", "limite", "barreira"],
                "sombras": ["rigidez", "aprisionamento", "bloqueio", "imobilidade"]
            },
            "mare": {
                "verbos": ["fluir", "alternar", "ciclar", "oscilar"],
                "qualidades": ["ritmo", "ciclo", "alternância", "movimento"],
                "sombras": ["inconstância", "instabilidade", "dispersão", "caos"]
            },
            "eco": {
                "verbos": ["retornar", "repetir", "ressonar", "amplificar"],
                "qualidades": ["memória", "insistência", "persistência", "retorno"],
                "sombras": ["obsessão", "repetição", "estagnação", "bloqueio"]
            },
            "lamina": {
                "verbos": ["cortar", "separar", "dividir", "decidir"],
                "qualidades": ["precisão", "decisão", "separação", "clareza"],
                "sombras": ["violência", "destruição", "ruptura", "perda"]
            }
        }
    
    def lexicalize(self, term: str, domain: str, type: str = "qualidade") -> str:
        if domain in self.domain_lexicon:
            lexicon = self.domain_lexicon[domain]
            terms_list = lexicon.get(f"{type}s", [])
            if terms_list and term.lower() in [t.lower() for t in terms_list]:
                return term
            if terms_list:
                return terms_list[0]
        return term


class Aggregator:
    def __init__(self):
        self.used_concepts: Set[Tuple[str, str, str, str]] = set()
        self.last_concept: Tuple[str, str, str, str] = None
    
    def can_add(self, qualidade: str, sombra: str, verbo: str, dominio: str) -> bool:
        concept = (qualidade.lower(), sombra.lower(), verbo.lower(), dominio.lower())
        
        if self.last_concept == concept:
            return False
        
        if concept in self.used_concepts and len(self.used_concepts) < 5:
            return False
        
        self.used_concepts.add(concept)
        self.last_concept = concept
        return True
    
    def reset(self):
        self.used_concepts.clear()
        self.last_concept = None
