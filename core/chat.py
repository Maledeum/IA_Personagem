import json
import requests

from core.memoria import carregar_memoria, salvar_memoria
from core.contexto import montar_contexto
from core.resumo import gerar_resumo_com_ia

# Caminho da personalidade base
PERSONALITY_FILE = "config/personality.txt"
LM_API_URL = "http://localhost:1234/v1/chat/completions"

# Carrega a personalidade do sistema
with open(PERSONALITY_FILE, "r", encoding="utf-8") as f:
    system_prompt = f.read()

# Variável global de memória
memoria = carregar_memoria()

def set_system_prompt(novo_prompt):
    global system_prompt
    system_prompt = novo_prompt

def conversar(pergunta):
    global memoria

    contexto_memoria = montar_contexto(memoria)
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

    # Salva a resposta completa após o yield
    memoria["conversa"].append({"role": "user", "content": pergunta})
    memoria["conversa"].append({"role": "assistant", "content": resposta})

    if memoria["contador_interacoes"] % 15 == 0:
        trechos = [f"{'Usuário' if m['role']=='user' else 'IA'}: {m['content']}" for m in memoria["conversa"]]
        resumo = gerar_resumo_com_ia(trechos)
        memoria["resumo_breve"].append(resumo)
        if len(memoria["resumo_breve"]) > 10:
            antigos = memoria["resumo_breve"][:3]
            resumo_antigo = gerar_resumo_com_ia(antigos)
            memoria["resumo_antigo"].append(resumo_antigo)
            memoria["resumo_breve"] = memoria["resumo_breve"][3:]

    salvar_memoria(memoria)
    return resposta