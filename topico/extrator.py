import re
import nltk
from nltk.corpus import stopwords

nltk.download("punkt", quiet=True)
nltk.download("stopwords", quiet=True)

stop_words = set(stopwords.words("portuguese"))

# === Configurações ===
DECAY = 1       # quanto decresce o peso a cada nova interação
MAX_TOPICOS = 5
MIN_PESO = 1    # elimina tópicos com peso abaixo disso

# === Extração por frequência e posição ===
def extrair_topicos(texto: str, max_topicos: int = 3):
    """Retorna lista com os *max_topicos* mais relevantes."""
    texto_limpo = re.sub(r"[^\w\s]", "", texto.lower())
    palavras = nltk.word_tokenize(texto_limpo)
    palavras_relevantes = [p for p in palavras if p not in stop_words and len(p) > 3]

    frequencia = {}
    for p in palavras_relevantes:
        frequencia[p] = frequencia.get(p, 0) + 1

    posicoes = {p: texto.lower().find(p) for p in frequencia}
    palavras_ordenadas = sorted(
        frequencia.items(), key=lambda x: (-x[1], posicoes.get(x[0], 9999))
    )

    return [p[0] for p in palavras_ordenadas[:max_topicos]]


def atualizar_topicos_ativos(memoria: dict, origem: str = "user", max_mensagens: int = 4):
    """Atualiza a lista de tópicos ativos na *memoria*."""
    memoria.setdefault("topicos_ativos", {})

    mensagens = memoria.get("conversa", [])[-max_mensagens:]
    texto_total = " ".join(
        m["content"] for m in mensagens if m.get("role") in ("user", "assistant")
    )
    novos = extrair_topicos(texto_total)

    for t in novos:
        if t in memoria["topicos_ativos"]:
            memoria["topicos_ativos"][t]["peso"] += 2
        else:
            memoria["topicos_ativos"][t] = {"peso": 3, "origem": origem}

    for t in list(memoria["topicos_ativos"].keys()):
        memoria["topicos_ativos"][t]["peso"] -= DECAY
        if memoria["topicos_ativos"][t]["peso"] < MIN_PESO:
            del memoria["topicos_ativos"][t]

    memoria["topicos_ativos"] = dict(
        sorted(memoria["topicos_ativos"].items(), key=lambda x: -x[1]["peso"])
    )
    memoria["topicos_ativos"] = dict(list(memoria["topicos_ativos"].items())[:MAX_TOPICOS])
