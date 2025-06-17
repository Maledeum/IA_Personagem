import json
import os
import requests

from core.memoria import (
    carregar_memoria,
    salvar_memoria,
    init_hierarchical,
    registrar_raw,
    gerar_resumo_episodio,
    gerar_resumo_branch,
    gerar_resumo_global,
    buscar_trechos,
    MAX_RESUMOS,
)
from core.contexto import montar_prompt
from topico.extrator import atualizar_topicos_ativos
from topico.contextualizador import contextualizar_pergunta
from core.resumo import (
    gerar_resumo_com_ia,
    resumo_episodio,
    resumo_branch,
    resumo_global,
)
from core.truncador import limitar_mensagens

# Caminho da personalidade base
DEFAULT_PERSONALITY_FILE = "config/personality.txt"
LM_API_URL = "http://localhost:1234/v1/chat/completions"

# Carrega a personalidade do sistema
with open(DEFAULT_PERSONALITY_FILE, "r", encoding="utf-8") as f:
    system_prompt = f.read()

# Modo de depuração controlado por variável de ambiente
DEBUG_CHAT = os.getenv("DEBUG_CHAT") == "1"

def set_debug(flag: bool) -> None:
    """Ativa ou desativa logs de depuração do chat."""
    global DEBUG_CHAT
    DEBUG_CHAT = flag

# Variáveis globais de memória
memory_base = os.path.join("memory", "default")
memory_file = os.path.join(memory_base, "working_memory.json")
init_hierarchical(memory_base)
memoria = carregar_memoria(memory_file)

# Últimos trechos recuperados pelo RAG
ultima_busca = []
ultima_metricas = {}

def get_ultima_busca():
    """Retorna os trechos recuperados mais recentemente."""
    return ultima_busca

def get_ultima_metricas():
    """Retorna as métricas de tokens da última chamada."""
    return ultima_metricas

def set_system_prompt(novo_prompt):
    global system_prompt
    system_prompt = novo_prompt

def set_memory_file(caminho):
    global memory_file, memoria, memory_base, ultima_busca
    memory_base = caminho
    memory_file = os.path.join(memory_base, "working_memory.json")
    init_hierarchical(memory_base)
    memoria = carregar_memoria(memory_file)
    ultima_busca = []

def carregar_personalidade(arquivo_json):
    with open(arquivo_json, "r", encoding="utf-8") as f:
        dados = json.load(f)
    set_system_prompt(dados.get("prompt", ""))
    nome = os.path.splitext(os.path.basename(arquivo_json))[0]
    set_memory_file(os.path.join("memory", nome))

def conversar(pergunta):
    global memoria, ultima_busca


    pergunta_ctx = contextualizar_pergunta(pergunta, memoria)
    # Usamos a pergunta enriquecida com tópicos apenas na busca por trechos
    # semelhantes. A pergunta original é enviada ao modelo de linguagem.
    ultima_busca = buscar_trechos(pergunta_ctx, memory_base)

    memoria["contador_interacoes"] += 1
    mensagens = montar_prompt(system_prompt, pergunta, memoria, rag_trechos=ultima_busca)
    mensagens, ultima_metricas_local = limitar_mensagens(mensagens, return_metrics=True)
    global ultima_metricas
    ultima_metricas = ultima_metricas_local or {}

    payload = {
        "model": "local-model",
        "messages": mensagens,
        "temperature": 0.7,
        "max_tokens": 3800,
        "stream": True
    }

    if DEBUG_CHAT:
        print("\n[DEBUG] Mensagens enviadas:")
        print(json.dumps(mensagens, ensure_ascii=False, indent=2))

    resposta = ""
    try:
        with requests.post(LM_API_URL, json=payload, stream=True) as response:
            for linha in response.iter_lines():
                if linha:
                    try:
                        linha = linha.decode("utf-8").strip()
                        if linha.startswith("data:"):
                            linha = linha[len("data:"):].strip()
                        if linha == "[DONE]":
                            break
                        data = json.loads(linha)
                        token = data["choices"][0]["delta"].get("content", "")
                        resposta += token
                        yield token
                    except Exception as e:
                        print(f"Erro ao processar linha da resposta: {e}")
                        continue
    except Exception as e:
        erro_msg = f"[Erro: não foi possível gerar resposta: {e}]"
        print(erro_msg)
        yield erro_msg
        return

    # Salva a resposta completa e registra em memória hierárquica
    memoria["conversa"].append({"role": "user", "content": pergunta})
    memoria["conversa"].append({"role": "assistant", "content": resposta})
    registrar_raw("user", pergunta, memory_base)
    registrar_raw("assistant", resposta, memory_base)

    resumo_ep = gerar_resumo_episodio(memory_base, resumo_episodio)
    if resumo_ep:
        memoria["resumo_breve"].append(resumo_ep)
        memoria["resumo_breve"] = memoria["resumo_breve"][-MAX_RESUMOS:]
    gerar_resumo_branch(memory_base, resumo_branch)
    gerar_resumo_global(memory_base, resumo_global)
    atualizar_topicos_ativos(memoria, origem="user")

    salvar_memoria(memoria, memory_file)
    return resposta
