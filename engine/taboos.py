from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class Taboo:
    id: str
    name: str
    response: str
    debt_delta: int
    entropy_delta: int
    cooldown_s: int
    alternative: str


def check_taboos(question: str, lore: dict) -> Tuple[Optional[Taboo], dict]:
    question_lower = question.lower()
    taboos_data = lore.get("taboos", [])
    
    for taboo_data in taboos_data:
        triggers = taboo_data.get("triggers", [])
        for trigger in triggers:
            if trigger.lower() in question_lower:
                return (
                    Taboo(
                        id=taboo_data.get("id", ""),
                        name=taboo_data.get("name", ""),
                        response=taboo_data.get("response", ""),
                        debt_delta=taboo_data.get("debt_delta", 0),
                        entropy_delta=taboo_data.get("entropy_delta", 0),
                        cooldown_s=taboo_data.get("cooldown_s", 0),
                        alternative=taboo_data.get("alternative", "")
                    ),
                    taboo_data
                )
    
    return None, {}
