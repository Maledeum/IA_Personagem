import os
from typing import List, Dict

import numpy as np

from core.embeddings import get_embedding
from core.memoria import _load_json, _save_json, _ler_raw_intervalo

_cache = {"base": None, "data": None}


def _cosine(a: List[float], b: List[float]) -> float:
    a = np.array(a)
    b = np.array(b)
    if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def carregar_indice(memory_base: str) -> List[Dict]:
    if _cache["base"] == memory_base and _cache["data"] is not None:
        return _cache["data"]
    arquivo = os.path.join(memory_base, "episodic_summaries.json")
    dados = _load_json(arquivo, [])
    _cache["base"] = memory_base
    _cache["data"] = dados
    return dados


def consultar_memoria(pergunta: str, memory_base: str, top_k: int = 3) -> List[Dict]:
    indice = carregar_indice(memory_base)
    if not indice:
        return []
    consulta_emb = get_embedding(pergunta)
    sims = []
    mudou = False
    for item in indice:
        emb = item.get("embedding")
        if not emb:
            emb = get_embedding(item.get("summary", ""))
            item["embedding"] = emb
            mudou = True
        score = _cosine(consulta_emb, emb)
        sims.append((score, item))
    if mudou:
        arquivo = os.path.join(memory_base, "episodic_summaries.json")
        _save_json(indice, arquivo)
    sims.sort(key=lambda x: x[0], reverse=True)
    resultados = []
    for score, item in sims[:top_k]:
        msgs = _ler_raw_intervalo(memory_base, item["start_id"], item["end_id"])
        resultados.append({
            "episodio": item["id"],
            "mensagens": msgs,
            "score": score,
        })
    return resultados
