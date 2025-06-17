import requests

LM_API_URL = "http://localhost:1234/v1/chat/completions"

def gerar_resumo_com_ia(trechos):
    prompt_resumo = "Resuma brevemente os principais tópicos da conversa a seguir e evite verbalizar muito:\n\n"
    texto_completo = prompt_resumo + "\n".join(trechos)

    payload = {
        "model": "local-model",
        "messages": [
            {"role": "user", "content": texto_completo}
        ],
        "temperature": 0.5,
        "max_tokens": 250
    }

    try:
        response = requests.post(LM_API_URL, json=payload, timeout=30)
        data = response.json()
        resposta = data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Erro ao gerar resumo: {e}")
        resposta = ""
    return resposta


def gerar_resumo_custom(trechos, prompt_resumo):
    texto_completo = prompt_resumo + "\n".join(trechos)
    payload = {
        "model": "local-model",
        "messages": [
            {"role": "user", "content": texto_completo}
        ],
        "temperature": 0.5,
        "max_tokens": 250
    }
    try:
        response = requests.post(LM_API_URL, json=payload, timeout=30)
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Erro ao gerar resumo customizado: {e}")
        return ""


def resumo_episodio(trechos):
    prompt = "Resuma em exatamente 7 tópicos os eventos a seguir, evite verbalizar e redundancia:\n\n"
    return gerar_resumo_custom(trechos, prompt)


def resumo_branch(trechos):
    prompt = "Contextualize os episódios em um parágrafo seguido de bullets:\n\n"
    return gerar_resumo_custom(trechos, prompt)


def resumo_global(trechos):
    prompt = "Faça uma visão geral da história em parágrafos curtos:\n\n"
    return gerar_resumo_custom(trechos, prompt)
