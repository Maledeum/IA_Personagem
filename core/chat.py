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
)
from core.contexto import montar_contexto
from core.resumo import (
    gerar_resumo_com_ia,
    resumo_episodio,
    resumo_branch,
    resumo_global,
)
from core.config import LM_API_URL
from core.rag import consultar_memoria

# Caminho da personalidade base
DEFAULT_PERSONALITY_FILE = "config/personality.txt"

# Carrega a personalidade do sistema
with open(DEFAULT_PERSONALITY_FILE, "r", encoding="utf-8") as f:
    system_prompt = f.read()

# Variáveis globais de memória
memory_base = os.path.join("memory", "default")
memory_file = os.path.join(memory_base, "working_memory.json")
init_hierarchical(memory_base)
memoria = carregar_memoria(memory_file)
ultima_memoria_rag = ""

def set_system_prompt(novo_prompt):
    global system_prompt
    system_prompt = novo_prompt

def set_memory_file(caminho):
    global memory_file, memoria, memory_base
    memory_base = caminho
    memory_file = os.path.join(memory_base, "working_memory.json")
    init_hierarchical(memory_base)
    memoria = carregar_memoria(memory_file)

def carregar_personalidade(arquivo_json):
    """Carrega dados da personalidade *arquivo_json* e atualiza a memória."""
    with open(arquivo_json, "r", encoding="utf-8") as f:
        dados = json.load(f)

    set_system_prompt(dados.get("prompt", ""))

    nome = os.path.splitext(os.path.basename(arquivo_json))[0]
    set_memory_file(os.path.join("memory", nome))

    # Mantém todos os campos, exceto o prompt, dentro de memoria["personagem"]
    atributos = {k: v for k, v in dados.items() if k != "prompt"}
    memoria.setdefault("personagem", {}).update(atributos)
    salvar_memoria(memoria, memory_file)

    return memoria["personagem"].get("nome", nome)

def carregar_usuario(arquivo_json):
    """Carrega dados do usuário *arquivo_json* e atualiza a memória."""
    if not os.path.exists(arquivo_json):
        return None
    with open(arquivo_json, "r", encoding="utf-8") as f:
        dados = json.load(f)
    memoria.setdefault("usuario", {}).update(dados)
    salvar_memoria(memoria, memory_file)
    return memoria["usuario"].get("nome", None)

def conversar(pergunta):
    global memoria, ultima_memoria_rag

    episodios = consultar_memoria(pergunta, memory_base, top_k=3)
    trechos = []
    for ep in episodios:
        texto = "\n".join(
            f"{'Usuário' if m['role']=='user' else 'IA'}: {m['content']}" for m in ep["mensagens"]
        )
        trechos.append(f"[Episódio {ep['episodio']}]\n{texto}")
    rag_texto = "\n\n".join(trechos)
    ultima_memoria_rag = rag_texto

    contexto_memoria = montar_contexto(memoria)
    if rag_texto:
        contexto_memoria = rag_texto + "\n\n" + contexto_memoria

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
            if response.status_code != 200:
                response.raise_for_status()
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
                    except Exception:
                        continue
    except requests.RequestException as exc:
        yield f"[Erro na requisição: {exc}]"
        return

    # Salva a resposta completa e registra em memória hierárquica
    memoria["conversa"].append({"role": "user", "content": pergunta})
    memoria["conversa"].append({"role": "assistant", "content": resposta})
    registrar_raw("user", pergunta, memory_base)
    registrar_raw("assistant", resposta, memory_base)

    resumo_ep = gerar_resumo_episodio(memory_base, resumo_episodio)
    if resumo_ep:
        memoria["resumo_breve"].append(resumo_ep)
    resumo_br = gerar_resumo_branch(memory_base, resumo_branch)
    if resumo_br:
        memoria["resumo_antigo"].append(resumo_br)
    gerar_resumo_global(memory_base, resumo_global)

    salvar_memoria(memoria, memory_file)
    return resposta