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
from core.contexto import montar_contexto
from core.resumo import (
    gerar_resumo_com_ia,
    resumo_episodio,
    resumo_branch,
    resumo_global,
)

# Caminho da personalidade base
DEFAULT_PERSONALITY_FILE = "config/personality.txt"
LM_API_URL = "http://localhost:1234/v1/chat/completions"

# Carrega a personalidade do sistema
with open(DEFAULT_PERSONALITY_FILE, "r", encoding="utf-8") as f:
    system_prompt = f.read()

# Variáveis globais de memória
memory_base = os.path.join("memory", "default")
memory_file = os.path.join(memory_base, "working_memory.json")
init_hierarchical(memory_base)
memoria = carregar_memoria(memory_file)

# Últimos trechos recuperados pelo RAG
ultima_busca = []

def get_ultima_busca():
    """Retorna os trechos recuperados mais recentemente."""
    return ultima_busca

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

    ultima_busca = buscar_trechos(pergunta, memory_base)

    contexto_memoria = montar_contexto(memoria)
    if ultima_busca:
        contexto_memoria += "\nTrechos relevantes:\n" + "\n----\n".join(ultima_busca)

    mensagens = [{"role": "system", "content": system_prompt + "\n\n" + contexto_memoria}]
    memoria["contador_interacoes"] += 1
    memoria["conversa"] = memoria.get("conversa", [])[-20:]
    mensagens.extend(memoria["conversa"])
    mensagens.append({"role": "user", "content": pergunta})

    payload = {
        "model": "local-model",
        "messages": mensagens,
        "temperature": 0.7,
        "max_tokens": 512,
        "stream": True
    }

    resposta = ""
    try:
        with requests.post(LM_API_URL, json=payload, stream=True) as response:
            for linha in response.iter_lines():
                if linha:
                    try:
                        linha = linha.decode("utf-8").replace("data: ", "")
                        if linha.strip() == "[DONE]":
                            break
                        data = json.loads(linha)
                        token = data["choices"][0]["delta"].get("content", "")
                        resposta += token
                        yield token
                    except:
                        continue
    except:
        yield "[Erro: não foi possível gerar resposta]"
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
    resumo_br = gerar_resumo_branch(memory_base, resumo_branch)
    if resumo_br:
        memoria["resumo_antigo"].append(resumo_br)
        memoria["resumo_antigo"] = memoria["resumo_antigo"][-MAX_RESUMOS:]
    gerar_resumo_global(memory_base, resumo_global)

    salvar_memoria(memoria, memory_file)
    return resposta