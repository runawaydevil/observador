from typing import Dict, List, Tuple, Optional
from enum import Enum
from .state import State
from .deck import Symbol
from .rng import SeededRNG


class DiscourseRelation(Enum):
    CAUSE = "CAUSE"
    CONDITION = "CONDITION"
    CONTRAST = "CONTRAST"
    ELABORATION = "ELABORATION"


class DiscoursePlanner:
    def __init__(self, rng: SeededRNG):
        self.rng = rng
    
    def select_relation(self, symbols: Tuple[Symbol, Symbol, Symbol]) -> DiscourseRelation:
        past, present, future = symbols
        
        past_polarity = past.polaridade
        present_polarity = present.polaridade
        future_polarity = future.polaridade
        
        past_domains = set(past.dominios)
        present_domains = set(present.dominios)
        future_domains = set(future.dominios)
        
        if past_domains & present_domains & future_domains:
            return DiscourseRelation.ELABORATION
        
        polarity_diff_past_present = abs(past_polarity - present_polarity)
        polarity_diff_present_future = abs(present_polarity - future_polarity)
        
        if polarity_diff_past_present < 0.2 and polarity_diff_present_future < 0.3:
            return DiscourseRelation.CAUSE
        
        if polarity_diff_past_present > 0.4 or polarity_diff_present_future > 0.5:
            return DiscourseRelation.CONTRAST
        
        if present.correspondencias.get("verbo") and future.correspondencias.get("qualidade"):
            return DiscourseRelation.CONDITION
        
        return self.rng.choice(list(DiscourseRelation))


class ContentPlanner:
    def extract_messages(self, symbol: Symbol) -> Dict:
        return {
            "pilar": symbol.correspondencias.get("qualidade", "ação"),
            "sombra": symbol.correspondencias.get("sombra", "limite"),
            "verbo": symbol.correspondencias.get("verbo", "age"),
            "elemento": symbol.correspondencias.get("elemento", ""),
            "condicao": self._extract_condition(symbol),
            "sinal": self._extract_signal(symbol),
            "sinais_observaveis": symbol.sinais_observaveis,
            "intervencoes_minimas": symbol.intervencoes_minimas,
            "excecoes": symbol.excecoes
        }
    
    def extract_observable_signals(self, symbol: Symbol, position: str) -> List[str]:
        return symbol.sinais_observaveis if symbol.sinais_observaveis else []
    
    def extract_interventions(self, symbol: Symbol) -> List[dict]:
        return symbol.intervencoes_minimas if symbol.intervencoes_minimas else []
    
    def extract_exceptions(self, symbol: Symbol) -> List[str]:
        return symbol.excecoes if symbol.excecoes else []
    
    def _extract_condition(self, symbol: Symbol) -> str:
        if symbol.contraindicacoes:
            return f"quando não há {symbol.contraindicacoes[0]}"
        return "quando necessário"
    
    def _extract_signal(self, symbol: Symbol) -> str:
        if symbol.gatilhos:
            return f"o sinal é {symbol.gatilhos[0]}"
        return "observe os padrões"


class SentencePlanner:
    def __init__(self, rng: SeededRNG):
        self.rng = rng
        self.symbol_references = {}
    
    def get_reference(self, symbol: Symbol, is_first: bool = False) -> str:
        if is_first:
            ref = f"{symbol.glifo} {symbol.nome}"
            self.symbol_references[symbol.id] = ref
            return ref
        
        if symbol.id in self.symbol_references:
            return self._get_subsequent_reference(symbol)
        
        ref = f"{symbol.glifo} {symbol.nome}"
        self.symbol_references[symbol.id] = ref
        return ref
    
    def _get_subsequent_reference(self, symbol: Symbol) -> str:
        apelidos = {
            "ferro": "o Ferro",
            "mare": "a Maré",
            "eco": "o Eco",
            "ferrugem": "a Ferrugem",
            "lamina": "a Lâmina",
            "porta": "a Porta",
            "espelho": "o Espelho",
            "no": "o Nó",
            "vazio": "o Vazio",
            "chama": "a Chama",
            "raiz": "a Raiz",
            "vento": "o Vento"
        }
        
        if symbol.id in apelidos:
            return apelidos[symbol.id]
        
        if symbol.nome.startswith("O "):
            return symbol.nome.lower()
        elif symbol.nome.startswith("A "):
            return symbol.nome.lower()
        
        return "isto"
    
    def get_connector(self, relation: DiscourseRelation) -> str:
        connectors_by_relation = {
            DiscourseRelation.CAUSE: ["porque", "logo", "por isso"],
            DiscourseRelation.CONDITION: ["se", "quando", "caso"],
            DiscourseRelation.CONTRAST: ["no entanto", "mas", "contudo"],
            DiscourseRelation.ELABORATION: ["assim", "dessa forma", "portanto"]
        }
        return self.rng.choice(connectors_by_relation.get(relation, ["então"]))


class CoherenceChecker:
    def check(self, reading_text: str, has_thesis: bool, has_tension: bool, 
              has_ato: bool, has_preco: bool) -> Dict[str, bool]:
        checks = {
            "has_thesis": has_thesis,
            "has_tension": has_tension,
            "has_ato": has_ato,
            "has_preco": has_preco,
            "no_explicit_contradiction": self._check_contradiction(reading_text),
            "readable_length": len(reading_text.split('\n')) <= 15
        }
        return checks
    
    def _check_contradiction(self, text: str) -> bool:
        text_lower = text.lower()
        contradictions = [
            ("faça", "não faça"),
            ("sim", "não"),
            ("sempre", "nunca")
        ]
        
        for pos, neg in contradictions:
            if pos in text_lower and neg in text_lower:
                pos_idx = text_lower.find(pos)
                neg_idx = text_lower.find(neg)
                if abs(pos_idx - neg_idx) < 100:
                    if "no entanto" not in text_lower[max(0, pos_idx-50):pos_idx+50]:
                        return False
        return True
    
    def is_valid(self, checks: Dict[str, bool]) -> bool:
        required = ["has_thesis", "has_tension", "has_ato", "has_preco"]
        return all(checks.get(key, False) for key in required) and checks.get("no_explicit_contradiction", True)


class ObjectiveLinter:
    def lint(self, reading_text: str, ato: str, preco: str) -> Dict:
        import re
        
        text_lower = reading_text.lower()
        lines = reading_text.split('\n')
        
        has_thesis = "tese:" in text_lower
        
        evidence_count = sum(1 for line in lines if "evidência:" in line.lower() or "observe:" in line.lower() or line.strip().startswith("Evidência"))
        
        warrant_connectors = ["por isso", "logo", "se", "caso", "no entanto", "regra:"]
        has_warrant = any(conn in text_lower for conn in warrant_connectors) or "regra:" in text_lower
        
        qualifier_words = ["provável", "possível", "se ", "caso", "quando"]
        has_qualifier = any(word in text_lower for word in qualifier_words)
        
        limit_indicators = ["limite:", "não confunda", "isto falha quando", "exceção"]
        has_limit = any(ind in text_lower for ind in limit_indicators)
        
        has_condition = "se" in text_lower and "então" in text_lower
        
        deadline_pattern = r'\b(hoje|24h|48h|\d+\s*dias?)\b'
        ato_has_deadline = bool(re.search(deadline_pattern, ato, re.IGNORECASE))
        preco_has_deadline = bool(re.search(deadline_pattern, preco, re.IGNORECASE))
        
        criterion_words = ["anote", "escreva", "liste", "observe", "documente", "registre", "identifique"]
        ato_has_criterion = any(word in ato.lower() for word in criterion_words)
        
        preco_is_concrete = not any(word in preco.lower() for word in ["moral", "espiritual", "abstrato"]) and ("renuncie" in preco.lower() or "não" in preco.lower())
        
        checks = {
            "has_thesis": has_thesis,
            "evidence_count": evidence_count,
            "evidence_count_ok": evidence_count >= 2,
            "has_warrant": has_warrant,
            "has_qualifier": has_qualifier,
            "has_limit": has_limit,
            "has_condition": has_condition,
            "ato_has_deadline": ato_has_deadline,
            "ato_has_criterion": ato_has_criterion,
            "preco_has_deadline": preco_has_deadline,
            "preco_is_concrete": preco_is_concrete
        }
        
        required_checks = [
            "has_thesis", "evidence_count_ok", "has_warrant", 
            "has_qualifier", "has_limit", "has_condition",
            "ato_has_deadline", "ato_has_criterion", 
            "preco_has_deadline", "preco_is_concrete"
        ]
        
        violations = [key for key in required_checks if not checks.get(key, False)]
        ok = len(violations) == 0
        
        return {
            "ok": ok,
            "checks": checks,
            "violations": violations
        }
