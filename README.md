# JARVIS local (Ollama + LangChain)

Agente pessoal rodando 100% local, com busca na internet e personalidade customizável.

## 1. Pré-requisitos (Ubuntu 24.04)

Se ainda não instalou o Ollama:

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:14b
```

Verifique se está rodando:

```bash
ollama list
```

## 2. Ambiente Python

Recomendado usar um virtualenv:

```bash
cd jarvis
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3. Rodar o agente

```bash
python jarvis_agent.py
```

Você verá um prompt de chat no terminal. Digite `sair` para encerrar.

Com `verbose=True` no `AgentExecutor`, o terminal mostra quando o JARVIS decide
usar a ferramenta de busca — útil pra depurar e entender o raciocínio dele.

## 4. Arquivos

| Arquivo             | O que é                                                   |
|----------------------|------------------------------------------------------------|
| `system_prompt.py`   | Personalidade do JARVIS — edite à vontade                 |
| `jarvis_agent.py`    | Agente LangChain: modelo + ferramentas + loop de chat      |
| `requirements.txt`   | Dependências Python                                        |

> **Nota:** o script usa a API nova do LangChain 1.0+ (`create_agent`, baseada
> em LangGraph), que substituiu `AgentExecutor`/`create_tool_calling_agent`
> (movidos para `langchain_classic`). A memória de conversa agora é gerenciada
> automaticamente por um `checkpointer` do LangGraph em vez de uma lista manual
> de mensagens.

## 5. Customizações comuns

**Trocar o modelo** (ex: se `qwen2.5:14b` estiver lento na sua 4060 8GB VRAM):
```python
llm = ChatOllama(model="llama3.1:8b", temperature=0.4)
```

**Adicionar mais ferramentas** — exemplo, ler um arquivo local, checar o clima,
controlar smart home, etc. Basta criar uma função decorada com `@tool` (veja o
exemplo `current_datetime` no `jarvis_agent.py`) e adicionar na lista `tools`.

**Ajustar personalidade** — edite `system_prompt.py`. É só texto, sem necessidade
de mexer no resto do código.

**Busca web melhor que DuckDuckGo** — se achar os resultados fracos, dá pra
trocar por Tavily (`langchain-tavily`) ou Brave Search, que têm resultados mais
ricos mas exigem API key gratuita.

## 6. Próximos passos sugeridos

- Adicionar memória persistente (SQLite ou arquivo) para o histórico sobreviver
  entre execuções — hoje ele reseta ao fechar o script.
- Plugar STT/TTS (Whisper + Piper) para virar assistente de voz.
- Rodar como serviço systemd para ligar junto com o sistema.

Se quiser ajuda com qualquer um desses passos, é só pedir.
