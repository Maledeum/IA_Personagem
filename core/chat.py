import os
import json
import requests
from datetime import datetime
from core.memory_manager import MemoryManager

# Caminho da personalidade base
PERSONALITY_FILE = os.path.join("config", "personality.txt")
LM_API_URL = os.getenv("LM_API_URL", "http://localhost:1234/v1/chat/completions")

# Carrega a personalidade do sistema
with open(PERSONALITY_FILE, "r", encoding="utf-8") as f:
    system_prompt = f.read()

# Gerenciador de memória para Aria (substitua 'aria' conforme necessário)
mem_manager = MemoryManager("aria")


def set_system_prompt(novo_prompt: str):
    global system_prompt
    system_prompt = novo_prompt


def conversar(pergunta: str):
    """
    Generator que envia tokens de resposta enquanto chama a API.
    Usa MemoryManager para contexto e registro de interações.
    """
    global mem_manager

    # 1) Registra mensagem do usuário
    mem_manager.record_interaction("user", pergunta, datetime.utcnow())

    # 2) Monta lista de mensagens para a API com contexto recente
    mensagens = [{"role": "system", "content": system_prompt}]
    recents = mem_manager.get_recent()  # últimas N interações
    for m in recents:
        role = m['speaker']
        # a API espera 'user' ou 'assistant'
        api_role = 'user' if role == 'user' else 'assistant'
        mensagens.append({"role": api_role, "content": m['text']})
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
                if not linha:
                    continue
                chunk = linha.decode('utf-8').replace('data: ', '')
                if chunk.strip() == '[DONE]':
                    break
                # usa json.loads do Python, não requests.utils.json
                data = json.loads(chunk)
                token = data['choices'][0]['delta'].get('content', '')
                resposta += token
                yield token
    except Exception as e:
        yield f"[Erro: não foi possível gerar resposta ({e})]"
        return

    # 3) Registra resposta completa
    mem_manager.record_interaction("assistant", resposta, datetime.utcnow())

    return resposta