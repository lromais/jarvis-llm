"""
JARVIS - Agente pessoal local rodando via Ollama + LangChain (API 1.0+, baseada em LangGraph).

Requisitos:
    - Ollama instalado e rodando (systemctl start ollama, ou já sobe sozinho)
    - Modelo baixado: ollama pull qwen2.5:14b
    - pip install -r requirements.txt

Uso:
    python jarvis_agent.py
"""

import datetime
import uuid

import requests
from bs4 import BeautifulSoup
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from ddgs import DDGS

from system_prompt import JARVIS_SYSTEM_PROMPT

# ---------------------------------------------------------------------------
# 0. CONFIGURAÇÃO DO USUÁRIO — edite aqui
# ---------------------------------------------------------------------------
# Usado para dar contexto de localização ao agente (buscas, cotações, clima etc).
USER_LOCATION = "Carapicuíba, São Paulo, Brasil"
USER_TIMEZONE = None  # None = usa o horário local da máquina

# ---------------------------------------------------------------------------
# 1. MODELO (o "cérebro")
# ---------------------------------------------------------------------------
llm = ChatOllama(
    model="qwen2.5:14b",
    temperature=0.4,
    num_ctx=8192,
)

# ---------------------------------------------------------------------------
# 2. FERRAMENTAS
# ---------------------------------------------------------------------------
@tool
def web_search(query: str) -> str:
    """Pesquisa na internet informações atuais: notícias, preços, cotações,
    eventos recentes ou qualquer coisa que possa ter mudado depois do
    treinamento do modelo. Use uma consulta curta e específica, e inclua
    o ano/data quando for relevante para o resultado (ex: 'cotação dólar hoje
    13 julho 2026')."""
    try:
        results = DDGS().text(query, max_results=8)
    except Exception as e:
        return f"Erro ao buscar: {e}"

    if not results:
        return "Nenhum resultado encontrado para essa busca."

    formatted = []
    for r in results:
        title = r.get("title", "")
        body = r.get("body", "")
        href = r.get("href", "")
        formatted.append(f"- {title}: {body} (fonte: {href})")
    return "\n".join(formatted)


@tool
def fetch_page(url: str) -> str:
    """Abre uma página web específica (normalmente uma URL retornada pelo
    web_search) e retorna o texto dela. Use isso sempre que o snippet do
    web_search não trouxer detalhes suficientes (ex: times de um jogo, data
    exata, placar, lista de itens) — não responda de forma vaga quando puder
    abrir a página e ler o conteúdo real."""
    try:
        resp = requests.get(
            url, timeout=10, headers={"User-Agent": "Mozilla/5.0"}
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = " ".join(soup.get_text(separator=" ").split())
        return text[:4000] if text else "Página sem conteúdo textual extraível."
    except Exception as e:
        return f"Erro ao abrir a página: {e}"


tools = [web_search, fetch_page]

# ---------------------------------------------------------------------------
# 3. MONTAGEM DO AGENTE
# ---------------------------------------------------------------------------
checkpointer = InMemorySaver()

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=JARVIS_SYSTEM_PROMPT,
    checkpointer=checkpointer,
)


def build_context_header() -> str:
    """Monta um cabeçalho com data/hora real e localização, injetado em toda
    mensagem para o agente nunca precisar 'adivinhar' isso da memória do
    treinamento (que fica desatualizada)."""
    now = datetime.datetime.now()
    dias = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
            "sexta-feira", "sábado", "domingo"]
    dia_semana = dias[now.weekday()]
    data_formatada = now.strftime(f"{dia_semana}, %d/%m/%Y às %H:%M")

    return (
        f"[Contexto automático — não mencione isto explicitamente ao usuário, "
        f"apenas use como fato: hoje é {data_formatada}. Localização aproximada "
        f"do usuário: {USER_LOCATION}. Se a pergunta envolver data, hora, "
        f"cotações, clima ou qualquer coisa 'atual', considere SEMPRE esta data "
        f"real acima, e não uma data da sua memória de treinamento. Ao pesquisar "
        f"na web, inclua a data/ano corretos na consulta quando fizer sentido. "
        f"NUNCA invente causas, motivos ou explicações que não estejam "
        f"literalmente nos resultados da busca — se a busca não trouxer o motivo "
        f"de algo, diga que não encontrou a explicação, não crie uma.]"
    )


# ---------------------------------------------------------------------------
# 4. LOOP DE CHAT
# ---------------------------------------------------------------------------
def chat_loop():
    print("=" * 60)
    print("JARVIS local — digite 'sair' para encerrar")
    print("=" * 60)

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    while True:
        try:
            user_input = input("\nVocê: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nJARVIS: Até mais, senhor(a).")
            break

        if not user_input:
            continue
        if user_input.lower() in {"sair", "exit", "quit"}:
            print("JARVIS: Até mais, senhor(a).")
            break

        # injeta data/hora real + localização em toda mensagem
        contextual_input = f"{build_context_header()}\n\n{user_input}"

        # recursion_limit alto o bastante para permitir várias buscas +
        # leituras de página em sequência antes da resposta final
        run_config = {**config, "recursion_limit": 50}

        result = agent.invoke(
            {"messages": [{"role": "user", "content": contextual_input}]},
            config=run_config,
        )

        final_message = result["messages"][-1]
        response = getattr(final_message, "content", final_message)

        print(f"\nJARVIS: {response}")


if __name__ == "__main__":
    chat_loop()
