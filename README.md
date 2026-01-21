# OBSERVADOR

Oráculo Web desenvolvido pela **0xpblab** — O Véu do Compasso.

Sistema de consulta oracular que utiliza símbolos, memória de estado e geração de linguagem natural estruturada (pipeline NLG baseado no modelo de argumentação Toulmin) para produzir leituras objetivas e coerentes.

## Características

- **Estrutura Toulmin**: Leituras com 10 linhas fixas (Tese, Passado, Evidências, Warrant, Condição, Tensão, Limite)
- **Memória de Estado**: Rastreia entropia, dívida, consultas anteriores e padrões
- **Sistema de Tabus**: Detecta e responde a perguntas proibidas (conselhos médicos, legais, etc.)
- **Re-geração Determinística**: Valida e regenera leituras até 3 vezes para garantir objetividade
- **Evidências Observáveis**: Usa sinais concretos específicos por símbolo
- **Intervenções Mínimas**: ATO e PREÇO ancorados em ações práticas com prazos

## Requisitos

- Python 3.11+
- Docker e Docker Compose (opcional)

## Instalação

### Local

```bash
pip install -r requirements.txt
```

### Docker

```bash
docker compose up -d --build
```

## Execução

### Local

```bash
python main.py
```

Acesse: http://localhost:9020

### Docker

```bash
docker compose up -d --build
```

Acesse: http://localhost:9020

Para ver logs:
```bash
docker compose logs -f
```

Para parar:
```bash
docker compose down
```

## Estrutura do Projeto

```
observador/
├── engine/              # Lógica do oráculo
│   ├── deck.py         # Gerenciamento de símbolos
│   ├── state.py        # Estado da sessão (entropia, dívida, memória)
│   ├── interpret.py    # Interpretação e geração de leituras
│   ├── nlg.py          # Pipeline NLG (ContentPlanner, SentencePlanner, ObjectiveLinter)
│   ├── microplanning.py # Lexicalizer e Aggregator
│   ├── topic_extractor.py # Extração de tópicos da pergunta
│   ├── rng.py          # RNG determinístico
│   └── taboos.py       # Sistema de tabus
├── web/                # Aplicação Flask
│   ├── app.py          # Factory da aplicação
│   ├── routes.py       # Rotas e lógica HTTP
│   ├── templates/      # Templates Jinja2
│   └── static/         # CSS, JS, assets
├── data/               # Dados do sistema
│   ├── lore.json       # Configuração da entidade
│   ├── deck.json       # 48 símbolos com sinais observáveis
│   └── templates.json  # Templates de geração de texto
├── storage/            # Dados gerados (gitignored)
│   ├── readings.jsonl  # Histórico de leituras
│   └── errors.log      # Log de erros
├── main.py             # Ponto de entrada
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Como Funciona

1. **Consulta**: Usuário faz uma pergunta
2. **Validação**: Sistema verifica tabus e penalidades
3. **Sorteio**: Seleciona 3 símbolos (passado, presente, tendência) baseado em:
   - Raridade do símbolo
   - Memória de consultas anteriores
   - Gatilhos na pergunta
4. **Planejamento Discursivo**: Seleciona relação (CAUSE, CONDITION, CONTRAST, ELABORATION)
5. **Geração**: Constrói leitura de 10 linhas usando:
   - Tese baseada na relação
   - Achados do passado/presente
   - Evidências observáveis dos símbolos
   - Warrant explícito
   - Condição com qualificador
   - Tensão e limite
6. **Validação**: ObjectiveLinter verifica estrutura Toulmin
7. **Re-geração**: Se falhar, regenera até 3 vezes com seeds diferentes
8. **ATO/PREÇO**: Gera ação prática e renúncia concreta

## Estrutura da Leitura

Cada leitura segue o formato:

```
[SELO]
[LITURGIA]
[LEITURA]
1. Tese: [claim baseado em relação]
2. Passado: [finding com qualidade+sombra]
3. Evidência: [sinal observável do passado]
4. Presente: [finding com verbo+qualidade+sombra]
5. Evidência: [sinal observável do presente]
6. Regra: [warrant explícito por relação]
7. Condição: [tendência condicional com qualificador]
8. Evidência: [sinal previsto do futuro]
9. Tensão: [conflito explícito]
10. Limite: [exceção ou aviso]
[CODA]
ATO: [ação prática com prazo]
PREÇO: [renúncia concreta com prazo]
```

## Porta

O sistema roda na porta **9020** (fixa).

## Dados Gerados

- `storage/readings.jsonl`: Histórico de todas as consultas (JSONL)
- `storage/errors.log`: Log de erros e exceções

Estes arquivos são ignorados pelo git (ver `.gitignore`).

## API

O sistema expõe uma API JSON em `/api/consult`:

```bash
curl -X POST http://localhost:9020/api/consult \
  -H "Content-Type: application/json" \
  -d '{"question": "Devo mudar de emprego?"}'
```

## Desenvolvido por

**0xpblab** — https://0xpblab.org

## Licença

[Especificar licença se aplicável]
