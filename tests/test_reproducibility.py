import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.rng import make_seed, SeededRNG
from engine.state import State


class TestReproducibility(unittest.TestCase):
    def test_seed_reproducibility(self):
        base = "test_base"
        question = "Teste de pergunta"
        count = 1
        
        seed1 = make_seed(base, question, count)
        seed2 = make_seed(base, question, count)
        
        self.assertEqual(seed1, seed2)
        
        rng1 = SeededRNG(seed1)
        rng2 = SeededRNG(seed2)
        
        val1 = [rng1.random() for _ in range(10)]
        val2 = [rng2.random() for _ in range(10)]
        
        self.assertEqual(val1, val2)
    
    def test_repeat_question_increases_entropy(self):
        state = State("test_base")
        initial_entropy = state.entropy
        initial_debt = state.debt
        
        question = "Teste"
        state.last_questions.append(question)
        state.apply_repeat_penalty()
        
        self.assertGreater(state.entropy, initial_entropy)
        self.assertGreater(state.debt, initial_debt)


if __name__ == '__main__':
    unittest.main()
