import requests

from core.config import LM_API_URL

def gerar_resumo_com_ia(trechos):
    prompt_resumo = "Resuma brevemente os principais tópicos da conversa a seguir:\n\n"
    texto_completo = prompt_resumo + "\n".join(trechos)

    payload = {
        "model": "local-model",
        "messages": [
            {"role": "user", "content": texto_completo}
        ],
        "temperature": 0.5,
        "max_tokens": 250
    }

    response = requests.post(LM_API_URL, json=payload)
    resposta = response.json()["choices"][0]["message"]["content"].strip()
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
    response = requests.post(LM_API_URL, json=payload)
    return response.json()["choices"][0]["message"]["content"].strip()


def resumo_episodio(trechos):
    prompt = "Resuma em exatamente 7 tópicos os eventos a seguir:\n\n"
    return gerar_resumo_custom(trechos, prompt)


def resumo_branch(trechos):
    prompt = "Contextualize os episódios em um parágrafo seguido de bullets:\n\n"
    return gerar_resumo_custom(trechos, prompt)


def resumo_global(trechos):
    prompt = "Faça uma visão geral da história em parágrafos curtos:\n\n"
    return gerar_resumo_custom(trechos, prompt)
