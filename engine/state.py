import hashlib
from typing import Optional


class State:
    def __init__(self, session_seed_base: str = None):
        if session_seed_base is None:
            import secrets
            session_seed_base = secrets.token_hex(16)
        self.session_seed_base = session_seed_base
        self.entropy = 0
        self.debt = 0
        self.consult_count = 0
        self.last_questions = []
        self.motif_counts = {}
        self.theme_counts = {}
        self.last_draw = []
        self.last_answer_hash = ""
    
    def check_repeat_question(self, question: str) -> bool:
        from .rng import normalize_question
        normalized = normalize_question(question)
        return normalized in self.last_questions
    
    def apply_repeat_penalty(self):
        self.entropy = min(100, self.entropy + 15)
        self.debt = min(100, self.debt + 10)
    
    def apply_certainty_penalty(self):
        self.debt = min(100, self.debt + 20)
    
    def apply_taboo_penalty(self, debt_delta: int, entropy_delta: int):
        self.debt = min(100, self.debt + debt_delta)
        self.entropy = min(100, self.entropy + entropy_delta)
    
    def update_memory(self, symbols: list, domains: list):
        for symbol_id in symbols:
            self.motif_counts[symbol_id] = self.motif_counts.get(symbol_id, 0) + 1
        for domain in domains:
            self.theme_counts[domain] = self.theme_counts.get(domain, 0) + 1
    
    def get_echo_symbol(self) -> Optional[str]:
        if not self.motif_counts:
            return None
        max_count = max(self.motif_counts.values())
        if max_count >= 2:
            for symbol_id, count in self.motif_counts.items():
                if count == max_count:
                    return symbol_id
        return None
    
    def to_dict(self):
        return {
            "session_seed_base": self.session_seed_base,
            "entropy": self.entropy,
            "debt": self.debt,
            "consult_count": self.consult_count,
            "last_questions": self.last_questions[-5:],
            "motif_counts": self.motif_counts,
            "theme_counts": self.theme_counts,
            "last_draw": self.last_draw,
            "last_answer_hash": self.last_answer_hash
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        state = cls(data.get("session_seed_base", ""))
        state.entropy = data.get("entropy", 0)
        state.debt = data.get("debt", 0)
        state.consult_count = data.get("consult_count", 0)
        state.last_questions = data.get("last_questions", [])
        state.motif_counts = data.get("motif_counts", {})
        state.theme_counts = data.get("theme_counts", {})
        state.last_draw = data.get("last_draw", [])
        state.last_answer_hash = data.get("last_answer_hash", "")
        return state
