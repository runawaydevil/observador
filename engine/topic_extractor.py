from typing import List, Tuple
from .deck import Deck


class TopicExtractor:
    def __init__(self, deck: Deck):
        self.deck = deck
        self.domain_keywords = self._build_domain_keywords()
    
    def _build_domain_keywords(self) -> dict:
        domain_map = {}
        for symbol in self.deck.symbols:
            for domain in symbol.dominios:
                if domain not in domain_map:
                    domain_map[domain] = []
                domain_map[domain].extend(symbol.gatilhos)
                domain_map[domain].append(domain)
        return domain_map
    
    def extract_topics(self, question: str) -> List[Tuple[str, float]]:
        question_lower = question.lower()
        topic_scores = {}
        
        for domain, keywords in self.domain_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in question_lower:
                    score += 1
            if score > 0:
                topic_scores[domain] = score
        
        sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_topics[:2]
    
    def get_primary_topic(self, question: str) -> str:
        topics = self.extract_topics(question)
        if topics:
            return topics[0][0]
        return "geral"
