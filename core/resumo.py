import requests

LM_API_URL = "http://localhost:1234/v1/chat/completions"

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