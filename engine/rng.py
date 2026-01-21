import random
import hashlib
import unicodedata
import re


def normalize_question(q: str) -> str:
    q = q.lower().strip()
    q = unicodedata.normalize('NFD', q)
    q = ''.join(c for c in q if unicodedata.category(c) != 'Mn')
    q = re.sub(r'\s+', ' ', q)
    return q


def make_seed(base: str, question: str, count: int, offer: str = "") -> int:
    normalized = normalize_question(question)
    combined = f"{base}:{normalized}:{count}:{offer}"
    hash_obj = hashlib.sha256(combined.encode('utf-8'))
    return int(hash_obj.hexdigest()[:16], 16)


class SeededRNG:
    def __init__(self, seed: int):
        self.rng = random.Random(seed)
    
    def random(self) -> float:
        return self.rng.random()
    
    def choice(self, seq):
        return self.rng.choice(seq)
    
    def choices(self, population, weights=None, k=1):
        return self.rng.choices(population, weights=weights, k=k)
    
    def randint(self, a, b):
        return self.rng.randint(a, b)
