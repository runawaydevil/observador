import json
from typing import Dict, Tuple, Optional
from .state import State
from .deck import Symbol
from .taboos import Taboo
from .rng import SeededRNG
from .nlg import DiscoursePlanner, DiscourseRelation, ContentPlanner, SentencePlanner, CoherenceChecker, ObjectiveLinter
from .topic_extractor import TopicExtractor


class Interpreter:
    def __init__(self, templates_path: str, deck=None):
        with open(templates_path, 'r', encoding='utf-8') as f:
            self.templates = json.load(f)
        self.deck = deck
        if deck:
            self.topic_extractor = TopicExtractor(deck)
        else:
            self.topic_extractor = None
    
    def interpret(self, state: State, symbols: Tuple[Symbol, Symbol, Symbol], 
                  taboo: Taboo, lore: dict, rng: SeededRNG, question: Optional[str] = None) -> Dict:
        past, present, future = symbols
        
        entity = lore["entity"]
        effects = lore.get("effects", {})
        voice = lore.get("voice", {})
        
        entropy_high = state.entropy > effects.get("interference_threshold", 60)
        debt_high = state.debt > 50
        echo_symbol = state.get_echo_symbol()
        has_eco = echo_symbol and any(s.id == echo_symbol for s in symbols)
        
        interference_markers = effects.get("interference_markers", ["░", "▒", "▓"])
        marker = rng.choice(interference_markers) if entropy_high else ""
        
        discourse_planner = DiscoursePlanner(rng)
        content_planner = ContentPlanner()
        sentence_planner = SentencePlanner(rng)
        
        relation = discourse_planner.select_relation(symbols)
        topic = self._extract_topic(question) if question and self.topic_extractor else "geral"
        
        seal = self._build_seal(entity, marker, entropy_high, debt_high)
        liturgy = self._build_liturgy(state, lore, marker, entropy_high, debt_high, echo_symbol, has_eco)
        MAX_ATTEMPTS = 3
        attempt = 0
        reading_result = None
        objective_checks = None
        ato = None
        preco = None
        
        while attempt < MAX_ATTEMPTS:
            seed_base = hash(str(state.session_seed_base) + str(question) + str(state.consult_count))
            seed_attempt = hash(str(seed_base) + str(attempt))
            rng_attempt = SeededRNG(seed_attempt)
            
            reading_result = self._build_reading(state, symbols, voice, marker, entropy_high, rng_attempt, 
                                                relation, content_planner, sentence_planner, has_eco, echo_symbol, attempt=attempt)
            ato_temp = self._generate_ato(symbols, rng_attempt, topic, present)
            preco_temp = self._generate_preco(symbols, rng_attempt, future)
            
            objective_linter = ObjectiveLinter()
            objective_checks = objective_linter.lint(reading_result["text"], ato_temp, preco_temp)
            
            if objective_checks["ok"]:
                ato = ato_temp
                preco = preco_temp
                break
            attempt += 1
        
        if ato is None:
            ato = ato_temp
            preco = preco_temp
        reading = reading_result["text"]
        interference_line = reading_result.get("interference_line", "")
        selected_evidence = reading_result.get("selected_evidence", {})
        ato = self._generate_ato(symbols, rng, topic, present)
        preco = self._generate_preco(symbols, rng, future)
        coda = self._build_coda(state, ato, preco, marker, entropy_high, debt_high)
        
        correspondencias = {
            "passado": {
                "nome": past.nome,
                "glifo": past.glifo,
                "elemento": past.correspondencias.get("elemento", ""),
                "planeta": past.correspondencias.get("planeta", ""),
                "qualidade": past.correspondencias.get("qualidade", ""),
                "verbo": past.correspondencias.get("verbo", ""),
                "sombra": past.correspondencias.get("sombra", "")
            },
            "presente": {
                "nome": present.nome,
                "glifo": present.glifo,
                "elemento": present.correspondencias.get("elemento", ""),
                "planeta": present.correspondencias.get("planeta", ""),
                "qualidade": present.correspondencias.get("qualidade", ""),
                "verbo": present.correspondencias.get("verbo", ""),
                "sombra": present.correspondencias.get("sombra", "")
            },
            "tendencia": {
                "nome": future.nome,
                "glifo": future.glifo,
                "elemento": future.correspondencias.get("elemento", ""),
                "planeta": future.correspondencias.get("planeta", ""),
                "qualidade": future.correspondencias.get("qualidade", ""),
                "verbo": future.correspondencias.get("verbo", ""),
                "sombra": future.correspondencias.get("sombra", "")
            }
        }
        
        result = {
            "seal": seal,
            "liturgy": liturgy,
            "reading": reading,
            "coda": coda,
            "ato": ato,
            "preco": preco,
            "correspondencias": correspondencias,
            "interference_line": interference_line,
            "relation": relation.value if hasattr(relation, 'value') else str(relation),
            "topic": topic,
            "attempt": attempt,
            "objective_checks": objective_checks or {},
            "selected_evidence": selected_evidence
        }
        
        return result
    
    def _build_seal(self, entity: dict, marker: str, entropy_high: bool, debt_high: bool) -> str:
        sig = entity["signature"]
        glyph = sig.get("seal_glyph", sig.get("seal_fallback", "<S>"))
        name = entity["name"]
        tagline = sig.get("tagline", "")
        
        if entropy_high:
            return f"[SELO]\n{marker} {name} — {tagline} {marker}"
        elif debt_high:
            return f"[SELO]\n{glyph} {name} — O preço aumenta."
        else:
            return f"[SELO]\n{glyph} {name} — {tagline}"
    
    def _build_liturgy(self, state: State, lore: dict, marker: str, 
                      entropy_high: bool, debt_high: bool, echo_symbol: str, has_eco: bool) -> str:
        laws = lore.get("laws", [])
        laws_applicable = ", ".join([l["id"] for l in laws[:3]])
        
        if entropy_high:
            return f"[LITURGIA]\n{marker} Interferência detectada. Leis: {laws_applicable}\nRuído: {state.entropy}%"
        elif debt_high:
            return f"[LITURGIA]\nLeis: {laws_applicable}\nDívida acumulada: {state.debt}%. O Véu endurece."
        elif has_eco and echo_symbol:
            return f"[LITURGIA]\nLeis: {laws_applicable} | Eco detectado: {echo_symbol}\nCusto: Entropia {state.entropy}%, Dívida {state.debt}%"
        else:
            return f"[LITURGIA]\nLeis aplicáveis: {laws_applicable}\nCusto do momento: Entropia {state.entropy}%, Dívida {state.debt}%"
    
    def _build_reading(self, state: State, symbols: Tuple[Symbol, Symbol, Symbol],
                      voice: dict, marker: str, entropy_high: bool, rng: SeededRNG,
                      relation: DiscourseRelation, content_planner: ContentPlanner,
                      sentence_planner: SentencePlanner, has_eco: bool, echo_symbol: Optional[str],
                      attempt: int = 0) -> Dict:
        past, present, future = symbols
        
        past_msg = content_planner.extract_messages(past)
        present_msg = content_planner.extract_messages(present)
        future_msg = content_planner.extract_messages(future)
        
        elemento = past_msg["elemento"] or "fogo"
        dominio_principal = present.dominios[0] if present.dominios else "geral"
        
        thesis_templates = self.templates.get("thesis_templates", {}).get(relation.value, [])
        if not thesis_templates:
            thesis_templates = ["Tese: {present_quality} no presente define a direção."]
        thesis = rng.choice(thesis_templates).format(
            past_quality=past_msg["pilar"],
            present_quality=present_msg["pilar"],
            future_quality=future_msg["pilar"],
            past_shadow=past_msg["sombra"],
            present_shadow=present_msg["sombra"],
            future_shadow=future_msg["sombra"],
            present_verbo=present_msg["verbo"]
        )
        
        finding_past_templates = self.templates.get("finding_past_templates", {}).get(elemento, [])
        if not finding_past_templates:
            finding_past_templates = ["Passado: {past_quality} se acumulou enquanto {past_shadow} crescia."]
        finding_past = rng.choice(finding_past_templates).format(
            past_quality=past_msg["pilar"],
            past_shadow=past_msg["sombra"]
        )
        
        evidence_past_signal = ""
        if past_msg["sinais_observaveis"]:
            evidence_past_signal = rng.choice(past_msg["sinais_observaveis"])
        else:
            evidence_past_signal = "padrões que se repetem no mesmo ponto"
        
        evidence_past_templates = self.templates.get("evidence_past_templates", ["Evidência: {sinal_observavel}"])
        evidence_1 = rng.choice(evidence_past_templates).format(sinal_observavel=evidence_past_signal)
        
        finding_present_templates = self.templates.get("finding_present_templates", {}).get(elemento, [])
        if not finding_present_templates:
            finding_present_templates = ["Presente: você {present_verbo} com {present_quality}, mas {present_shadow} ameaça."]
        finding_present = rng.choice(finding_present_templates).format(
            presente_verbo=present_msg["verbo"],
            present_verbo=present_msg["verbo"],
            presente_quality=present_msg["pilar"],
            present_quality=present_msg["pilar"],
            presente_shadow=present_msg["sombra"],
            present_shadow=present_msg["sombra"]
        )
        
        evidence_present_signal = ""
        if present_msg["sinais_observaveis"]:
            evidence_present_signal = rng.choice(present_msg["sinais_observaveis"])
        else:
            evidence_present_signal = "sinais observáveis no presente"
        
        evidence_present_templates = self.templates.get("evidence_present_templates", ["Evidência: {sinal_observavel}"])
        evidence_2 = rng.choice(evidence_present_templates).format(sinal_observavel=evidence_present_signal)
        
        warrant_templates = self.templates.get("warrant_by_relation", {}).get(relation.value, [])
        if not warrant_templates:
            warrant_templates = [f"Regra: {sentence_planner.get_connector(relation)}, {present_msg['pilar']} continua {past_msg['pilar']}."]
        warrant = rng.choice(warrant_templates).format(
            presente_verbo=present_msg["verbo"],
            present_verbo=present_msg["verbo"],
            passado_qualidade=past_msg["pilar"],
            past_qualidade=past_msg["pilar"],
            presente_qualidade=present_msg["pilar"],
            present_qualidade=present_msg["pilar"],
            tend_sombra=future_msg["sombra"],
            futuro_qualidade=future_msg["pilar"],
            dominio=dominio_principal
        )
        
        qualifier_templates = self.templates.get("qualifier_templates", ["provável", "possível"])
        qualifier = rng.choice(qualifier_templates)
        
        trend_templates = self.templates.get("trend_sentence_templates", {}).get(elemento, [])
        if not trend_templates:
            trend_templates = [f"Se você manter {{present_quality}}, a tendência é {{future_quality}}, mas {{future_shadow}} cresce."]
        condition_trend = rng.choice(trend_templates).format(
            present_quality=present_msg["pilar"],
            present_verbo=present_msg["verbo"],
            future_quality=future_msg["pilar"],
            future_shadow=future_msg["sombra"]
        )
        condition_trend = f"Condição ({qualifier}): {condition_trend}"
        
        evidence_future_signal = ""
        if future_msg["sinais_observaveis"]:
            evidence_future_signal = rng.choice(future_msg["sinais_observaveis"])
        else:
            evidence_future_signal = "sinais prováveis no futuro"
        
        if has_eco and echo_symbol:
            eco_templates = self.templates.get("eco_templates", [])
            if eco_templates:
                evidence_3 = rng.choice(eco_templates).format(echo_symbol=echo_symbol)
            else:
                evidence_future_templates = self.templates.get("evidence_future_templates", ["Evidência prevista: {sinal_observavel}"])
                evidence_3 = rng.choice(evidence_future_templates).format(sinal_observavel=evidence_future_signal)
        else:
            evidence_future_templates = self.templates.get("evidence_future_templates", ["Evidência prevista: {sinal_observavel}"])
            evidence_3 = rng.choice(evidence_future_templates).format(sinal_observavel=evidence_future_signal)
        
        tension_templates = self.templates.get("tension_templates", [])
        if not tension_templates:
            tension_templates = ["Tensão: {present_quality} versus {future_shadow}."]
        tension = rng.choice(tension_templates).format(
            past_quality=past_msg["pilar"],
            present_quality=present_msg["pilar"],
            future_quality=future_msg["pilar"],
            past_shadow=past_msg["sombra"],
            present_shadow=present_msg["sombra"],
            future_shadow=future_msg["sombra"]
        )
        
        limit_text = ""
        if present_msg["excecoes"]:
            limit_text = f"Limite: {rng.choice(present_msg['excecoes'])}"
        else:
            limit_templates = self.templates.get("limit_templates", ["Limite: não confunda tendência com certeza."])
            limit_text = rng.choice(limit_templates).format(
                present_quality=present_msg["pilar"],
                present_shadow=present_msg["sombra"],
                past_quality=past_msg["pilar"],
                future_quality=future_msg["pilar"]
            )
        
        lines = [
            "[LEITURA]",
            thesis,
            finding_past,
            evidence_1,
            finding_present,
            evidence_2,
            warrant,
            condition_trend,
            evidence_3,
            tension,
            limit_text
        ]
        
        reading_text = "\n".join(lines)
        
        interference_line = ""
        if entropy_high:
            fragments = self.templates.get("interference_fragments", ["░", "▒", "▓"])
            frag = rng.choice(fragments)
            interference_line = f"[INTERFERÊNCIA] {frag} eco… eco… {frag}"
        
        return {
            "text": reading_text,
            "interference_line": interference_line,
            "selected_evidence": {
                "past": evidence_past_signal,
                "present": evidence_present_signal,
                "future": evidence_future_signal
            }
        }
    
    def _build_coda(self, state: State, ato: str, preco: str,
                   marker: str, entropy_high: bool, debt_high: bool) -> str:
        if debt_high:
            return f"[CODA]\nATO: {ato}\nPREÇO: {preco} (Dívida acumulada: {state.debt}%)"
        else:
            return f"[CODA]\nATO: {ato}\nPREÇO: {preco}"
    
    def _generate_ato(self, symbols: Tuple[Symbol, Symbol, Symbol], rng: SeededRNG, 
                     topic: str, present: Symbol) -> str:
        if present.intervencoes_minimas:
            intervention = rng.choice(present.intervencoes_minimas)
            prazo_horas = intervention.get("prazo_horas", 24)
            acao = intervention.get("acao", "execute uma ação")
            
            if prazo_horas == 24:
                prazo_str = "24h"
            elif prazo_horas == 48:
                prazo_str = "48h"
            elif prazo_horas <= 12:
                prazo_str = "hoje"
            else:
                prazo_str = f"{prazo_horas}h"
            
            templates = self.templates.get("ato_templates", [])
            if templates and "{acao}" in templates[0]:
                template = rng.choice([t for t in templates if "{acao}" in t] or templates)
                return template.format(acao=acao, tema=topic, prazo_horas=prazo_horas, prazo=prazo_str)
            else:
                return f"Em {prazo_str}, {acao} sobre {topic}."
        
        templates = self.templates.get("ato_templates", [])
        if not templates:
            templates = ["Hoje, faça uma ação pequena de {verbo} sobre {tema}: {passo}."]
        template = rng.choice(templates)
        verbo = present.correspondencias.get("verbo", "agir")
        passos = self.templates.get("passos_observaveis", ["anote 3 evidências"])
        passo = rng.choice(passos)
        return template.format(verbo=verbo, tema=topic, passo=passo)
    
    def _generate_preco(self, symbols: Tuple[Symbol, Symbol, Symbol], rng: SeededRNG, 
                       future: Symbol) -> str:
        templates = self.templates.get("preco_templates", [])
        if not templates:
            templates = ["Por {prazo}, renuncie a {renuncia} — para que {sombra} não governe."]
        template = rng.choice(templates)
        sombra = future.correspondencias.get("sombra", "algo")
        qualidade = future.correspondencias.get("qualidade", "algo")
        time_refs = self.templates.get("time_references", ["48h", "24h", "3 dias"])
        renuncias = self.templates.get("renuncias", ["perguntar de novo por 48h"])
        prazo = rng.choice(time_refs)
        renuncia = rng.choice(renuncias)
        
        if sombra == "rigidez":
            renuncia = "controle excessivo" if "controle" not in renuncia else renuncia
        elif sombra == "dispersão":
            renuncia = "multitarefa" if "multitarefa" not in renuncia else renuncia
        elif sombra == "obsessão":
            renuncia = "repetir a mesma pergunta" if "pergunta" not in renuncia else renuncia
        
        acao_proibida = "perguntar de novo" if "perguntar" in renuncia else ("repetir" if "repetir" in renuncia else "fazer")
        return template.format(
            prazo=prazo, renuncia=renuncia, sombra=sombra, 
            qualidade=qualidade, acao_proibida=acao_proibida
        )
    
    def _extract_topic(self, question: str) -> str:
        if self.topic_extractor:
            return self.topic_extractor.get_primary_topic(question)
        return "geral"
