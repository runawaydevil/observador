from flask import Blueprint, render_template, request, session, jsonify, current_app
from pathlib import Path
import json
import time
from datetime import datetime
from engine.state import State
from engine.rng import make_seed, SeededRNG
from engine.taboos import check_taboos

bp = Blueprint('observador', __name__)


def get_state():
    if 'session_seed_base' not in session:
        import secrets
        session['session_seed_base'] = secrets.token_hex(16)
        session['state'] = State(session['session_seed_base']).to_dict()
    
    state = State.from_dict(session['state'])
    return state


def save_state(state):
    session['state'] = state.to_dict()


def render_reading_to_html(reading_data, entropy_high=False):
    correspondencias = reading_data.get('correspondencias', {})
    
    container_class = 'reading-container'
    if entropy_high:
        container_class += ' entropy-high'
    
    html = f'<div class="{container_class}">'
    
    if correspondencias:
        html += '<div class="correspondences-table">'
        html += '<table><thead><tr><th>Posição</th><th>Símbolo</th><th>Elemento</th><th>Planeta</th><th>Qualidade</th></tr></thead><tbody>'
        for pos, key in [("Passado", "passado"), ("Presente", "presente"), ("Tendência", "tendencia")]:
            if key in correspondencias:
                sym = correspondencias[key]
                html += f'<tr><td>{pos}</td><td>{sym.get("glifo", "")} {sym.get("nome", "")}</td><td>{sym.get("elemento", "")}</td><td>{sym.get("planeta", "")}</td><td>{sym.get("qualidade", "")}</td></tr>'
        html += '</tbody></table></div>'
    
    seal = reading_data.get('seal', '').replace('\n', '<br>')
    liturgy = reading_data.get('liturgy', '').replace('\n', '<br>')
    reading = reading_data.get('reading', '').replace('\n', '<br>')
    coda = reading_data.get('coda', '').replace('\n', '<br>')
    interference_line = reading_data.get('interference_line', '')
    
    glitch_class = 'glitch' if entropy_high else ''
    
    html += f'<div class="seal {glitch_class}">{seal}</div>'
    html += f'<div class="liturgy {glitch_class}">{liturgy}</div>'
    
    if interference_line:
        html += f'<div class="interference-line">{interference_line}</div>'
    
    html += f'<div class="reading-text {glitch_class}">{reading}</div>'
    html += f'<div class="coda {glitch_class}">{coda}</div>'
    
    ato = reading_data.get('ato', '')
    preco = reading_data.get('preco', '')
    html += f'<div class="summary"><div class="ato">ATO: {ato}</div><div class="preco">PREÇO: {preco}</div></div>'
    
    html += '</div>'
    return html


@bp.route('/')
def home():
    return render_template('home.html')


@bp.route('/consult', methods=['GET', 'POST'])
def consult():
    if request.method == 'GET':
        return render_template('consult.html')
    
    question = request.form.get('question', '').strip()
    if not question:
        return render_template('consult.html', error="Pergunta vazia.")
    
    state = get_state()
    lore = current_app.config['LORE']
    deck = current_app.config['DECK']
    interpreter = current_app.config['INTERPRETER']
    base_path = current_app.config['BASE_PATH']
    
    taboo, taboo_data = check_taboos(question, lore)
    
    if taboo and taboo.id == "T6":
        save_state(state)
        return render_template('consult.html', 
                             taboo_response="Eu não selo portas finais.",
                             taboo_alternative="Procure ajuda agora. Se houver risco imediato, ligue para serviços de emergência locais.",
                             is_crisis=True)
    
    if taboo:
        state.apply_taboo_penalty(taboo.debt_delta, taboo.entropy_delta)
        save_state(state)
        return render_template('consult.html',
                             taboo_response=taboo.response,
                             taboo_alternative=taboo.alternative)
    
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
    
    reading_data = interpreter.interpret(state, symbols, taboo, lore, rng, question=question)
    
    state.last_answer_hash = str(hash(str(reading_data)))
    
    entropy_high = state.entropy > lore.get('effects', {}).get('interference_threshold', 60)
    reading_html = render_reading_to_html(reading_data, entropy_high)
    
    save_state(state)
    
    storage_path = base_path / "storage" / "readings.jsonl"
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
            "preco": reading_data["preco"],
            "relation": reading_data.get("relation", ""),
            "topic": reading_data.get("topic", ""),
            "objective_checks": reading_data.get("objective_checks", {}),
            "attempt": reading_data.get("attempt", 0),
            "selected_evidence": reading_data.get("selected_evidence", {}),
            "interference_line": reading_data.get("interference_line", "")
        }
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    return render_template('consult.html', 
                         reading_html=reading_html,
                         entropy=state.entropy,
                         debt=state.debt,
                         entropy_high=entropy_high)


@bp.route('/register')
def register():
    base_path = current_app.config['BASE_PATH']
    storage_path = base_path / "storage" / "readings.jsonl"
    
    readings = []
    if storage_path.exists():
        with open(storage_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    readings.append(json.loads(line))
    
    readings.reverse()
    
    for reading in readings:
        timestamp = reading.get("timestamp", 0)
        dt = datetime.fromtimestamp(timestamp)
        reading['formatted_time'] = dt.strftime('%Y-%m-%d %H:%M')
    
    return render_template('register.html', readings=readings[:20])


@bp.route('/api/consult', methods=['POST'])
def api_consult():
    data = request.get_json()
    question = data.get('question', '').strip() if data else ''
    
    if not question:
        return jsonify({"error": "Pergunta vazia."}), 400
    
    state = get_state()
    lore = current_app.config['LORE']
    deck = current_app.config['DECK']
    interpreter = current_app.config['INTERPRETER']
    base_path = current_app.config['BASE_PATH']
    
    taboo, _ = check_taboos(question, lore)
    
    if taboo and taboo.id == "T6":
        save_state(state)
        return jsonify({
            "crisis": True,
            "response": "Eu não selo portas finais.",
            "alternative": "Procure ajuda agora. Se houver risco imediato, ligue para serviços de emergência locais."
        })
    
    if taboo:
        state.apply_taboo_penalty(taboo.debt_delta, taboo.entropy_delta)
        save_state(state)
        return jsonify({
            "taboo": True,
            "response": taboo.response,
            "alternative": taboo.alternative
        })
    
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
    
    reading_data = interpreter.interpret(state, symbols, taboo, lore, rng, question=question)
    state.last_answer_hash = str(hash(str(reading_data)))
    
    entropy_high = state.entropy > lore.get('effects', {}).get('interference_threshold', 60)
    
    save_state(state)
    
    storage_path = base_path / "storage" / "readings.jsonl"
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
            "preco": reading_data["preco"],
            "relation": reading_data.get("relation", ""),
            "topic": reading_data.get("topic", ""),
            "objective_checks": reading_data.get("objective_checks", {}),
            "attempt": reading_data.get("attempt", 0),
            "selected_evidence": reading_data.get("selected_evidence", {}),
            "interference_line": reading_data.get("interference_line", "")
        }
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    return jsonify({
        "reading": reading_data,
        "entropy": state.entropy,
        "debt": state.debt,
        "entropy_high": entropy_high
    })


@bp.route('/sitemap.xml')
def sitemap():
    from flask import url_for
    base_url = request.url_root.rstrip('/')
    
    urls = [
        {
            'loc': base_url + url_for('observador.home'),
            'changefreq': 'weekly',
            'priority': '1.0'
        },
        {
            'loc': base_url + url_for('observador.consult'),
            'changefreq': 'daily',
            'priority': '0.9'
        },
        {
            'loc': base_url + url_for('observador.register'),
            'changefreq': 'daily',
            'priority': '0.8'
        }
    ]
    
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for url in urls:
        sitemap_xml += '  <url>\n'
        sitemap_xml += f'    <loc>{url["loc"]}</loc>\n'
        sitemap_xml += f'    <changefreq>{url["changefreq"]}</changefreq>\n'
        sitemap_xml += f'    <priority>{url["priority"]}</priority>\n'
        sitemap_xml += '  </url>\n'
    
    sitemap_xml += '</urlset>'
    
    from flask import Response
    return Response(sitemap_xml, mimetype='application/xml')


@bp.route('/robots.txt')
def robots():
    base_url = request.url_root.rstrip('/')
    robots_txt = f"""User-agent: *
Allow: /
Disallow: /api/
Disallow: /storage/

Sitemap: {base_url}/sitemap.xml
"""
    from flask import Response
    return Response(robots_txt, mimetype='text/plain')
