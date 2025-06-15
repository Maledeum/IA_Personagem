# memoria.py
import json
import os
import warnings
import shutil
import hashlib
from typing import List, Tuple

try:
    import faiss  # type: ignore
    _HAVE_FAISS = True
except Exception:  # pragma: no cover - optional dependency
    faiss = None
    _HAVE_FAISS = False

DEFAULT_MEMORY_DIR = "memory"
DEFAULT_MEMORY_FILE = os.path.join(DEFAULT_MEMORY_DIR, "working_memory.json")

RAW_ROTATE = 500  # mensagens por arquivo raw
EPISODE_SIZE = 10
EPISODES_PER_BRANCH = 4
BRANCHES_PER_GLOBAL = 4
VECTOR_DIR_NAME = "vectors"
EPISODIC_VECTOR_FILE = "episodic_vectors.json"
HISTORICAL_VECTOR_FILE = "historical_vectors.json"
RAW_VECTOR_FILE = "raw_vectors.json"
RAW_CHUNK_VECTOR_FILE = "raw_chunk_vectors.json"
EPISODIC_FAISS_FILE = "episodic_vectors.faiss"
RAW_FAISS_FILE = "raw_vectors.faiss"
RAW_CHUNK_FAISS_FILE = "raw_chunks.faiss"
MAX_RESUMOS = 5


def _text_embedding(text, size=32):
    """Return a deterministic embedding list for *text*."""
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return [b / 255 for b in digest[:size]]


def dividir_em_chunks(texto: str, max_tokens: int = 64) -> List[str]:
    """Divide *texto* em chunks de até *max_tokens* palavras."""
    import re

    sentencas = re.split(r"(?<=[.!?]) +", texto)
    chunks = []
    atual = ""
    for s in sentencas:
        if len(atual.split()) + len(s.split()) <= max_tokens:
            atual = f"{atual} {s}".strip()
        else:
            if atual:
                chunks.append(atual)
            atual = s
    if atual:
        chunks.append(atual.strip())
    return chunks


def init_vector_store(base_dir):
    """Ensure the vector directory exists for this personality."""
    path = os.path.join(base_dir, VECTOR_DIR_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def _faiss_paths(base_dir: str, filename: str) -> Tuple[str, str]:
    directory = init_vector_store(base_dir)
    index_path = os.path.join(directory, filename)
    id_path = index_path + "_ids.json"
    return index_path, id_path


def _faiss_add_vector(base_dir: str, filename: str, vec: List[float], item_id: int) -> None:
    if not _HAVE_FAISS:
        return
    import numpy as np

    index_path, id_path = _faiss_paths(base_dir, filename)
    if os.path.exists(index_path):
        index = faiss.read_index(index_path)
        ids = _load_json(id_path, [])
    else:
        index = faiss.IndexFlatIP(len(vec))
        ids = []
    index.add(np.array([vec], dtype="float32"))
    ids.append(item_id)
    faiss.write_index(index, index_path)
    _save_json(ids, id_path)


def _faiss_search(base_dir: str, filename: str, vec: List[float], top_n: int) -> List[int]:
    if not _HAVE_FAISS:
        return []
    import numpy as np

    index_path, id_path = _faiss_paths(base_dir, filename)
    if not os.path.exists(index_path):
        return []
    index = faiss.read_index(index_path)
    ids = _load_json(id_path, [])
    if not ids:
        return []
    D, I = index.search(np.array([vec], dtype="float32"), top_n)
    result = []
    for idx in I[0]:
        if 0 <= idx < len(ids):
            result.append(ids[idx])
    return result


def add_episodic_embedding(base_dir, episodic_id, resumo):
    """Append embedding for a new episodic summary."""
    emb_dir = init_vector_store(base_dir)
    file_path = os.path.join(emb_dir, EPISODIC_VECTOR_FILE)
    data = _load_json(file_path, [])
    emb = _text_embedding(resumo)
    data.append({"id": episodic_id, "embedding": emb})
    _save_json(data, file_path)
    _faiss_add_vector(base_dir, EPISODIC_FAISS_FILE, emb, episodic_id)


def add_raw_embedding(base_dir: str, msg_id: int, content: str) -> None:
    """Store embedding for a raw message."""
    emb_dir = init_vector_store(base_dir)
    file_path = os.path.join(emb_dir, RAW_VECTOR_FILE)
    data = _load_json(file_path, [])
    emb = _text_embedding(content)
    data.append({"id": msg_id, "embedding": emb})
    _save_json(data, file_path)
    _faiss_add_vector(base_dir, RAW_FAISS_FILE, emb, msg_id)


def add_raw_chunk_embeddings(base_dir: str, msg_id: int, content: str) -> None:
    """Store embeddings for each chunk of a raw message."""
    emb_dir = init_vector_store(base_dir)
    file_path = os.path.join(emb_dir, RAW_CHUNK_VECTOR_FILE)
    data = _load_json(file_path, [])
    for pos, chunk in enumerate(dividir_em_chunks(content)):
        emb = _text_embedding(chunk)
        cid = f"{msg_id}_{pos}"
        data.append({"id": cid, "raw_id": msg_id, "pos": pos, "text": chunk, "embedding": emb})
        _faiss_add_vector(base_dir, RAW_CHUNK_FAISS_FILE, emb, cid)
    _save_json(data, file_path)


def rebuild_episodic_embeddings(base_dir):
    """Recalculate embeddings for all episodic summaries."""
    emb_dir = init_vector_store(base_dir)
    file_path = os.path.join(emb_dir, EPISODIC_VECTOR_FILE)
    episodios = _load_json(os.path.join(base_dir, "episodic_summaries.json"), [])
    data = [{"id": e["id"], "embedding": _text_embedding(e["summary"])} for e in episodios]
    _save_json(data, file_path)
    if _HAVE_FAISS:
        index_path, _ = _faiss_paths(base_dir, EPISODIC_FAISS_FILE)
        if os.path.exists(index_path):
            os.remove(index_path)
        for item in data:
            _faiss_add_vector(base_dir, EPISODIC_FAISS_FILE, item["embedding"], item["id"])


def rebuild_historical_embeddings(base_dir):
    """Recalculate embeddings for all historical summaries."""
    emb_dir = init_vector_store(base_dir)
    file_path = os.path.join(emb_dir, HISTORICAL_VECTOR_FILE)
    historicos = _load_json(os.path.join(base_dir, "historical_summaries.json"), [])
    data = [{"id": h["id"], "embedding": _text_embedding(h["summary"])} for h in historicos]
    _save_json(data, file_path)


def rebuild_raw_embeddings(base_dir: str) -> None:
    """Recalculate embeddings for all raw messages."""
    emb_dir = init_vector_store(base_dir)
    file_path = os.path.join(emb_dir, RAW_VECTOR_FILE)
    chunk_path = os.path.join(emb_dir, RAW_CHUNK_VECTOR_FILE)
    meta = _load_meta(base_dir)
    data = []
    chunk_data = []
    for idx in range(1, meta["last_id"] + 1):
        mensagens = _ler_raw_intervalo(base_dir, idx, idx)
        if mensagens:
            m = mensagens[0]
            data.append({"id": m["id"], "embedding": _text_embedding(m["content"])})
            for pos, chunk in enumerate(dividir_em_chunks(m["content"])):
                chunk_data.append({
                    "id": f"{m['id']}_{pos}",
                    "raw_id": m["id"],
                    "pos": pos,
                    "text": chunk,
                    "embedding": _text_embedding(chunk),
                })
    _save_json(data, file_path)
    _save_json(chunk_data, chunk_path)
    if _HAVE_FAISS:
        index_path, _ = _faiss_paths(base_dir, RAW_FAISS_FILE)
        if os.path.exists(index_path):
            os.remove(index_path)
        for item in data:
            _faiss_add_vector(base_dir, RAW_FAISS_FILE, item["embedding"], item["id"])

        index_path2, _ = _faiss_paths(base_dir, RAW_CHUNK_FAISS_FILE)
        if os.path.exists(index_path2):
            os.remove(index_path2)
        for item in chunk_data:
            _faiss_add_vector(base_dir, RAW_CHUNK_FAISS_FILE, item["embedding"], item["id"])


def _cosine_similarity(a, b):
    """Calculate cosine similarity between two vectors."""
    import math

    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def buscar_trechos(query, base_dir, top_n=6):
    """Retorna os *top_n* trechos mais similares ao *query*.

    A busca agora é feita diretamente sobre os embeddings dos chunks de
    mensagens brutas, permitindo recuperar trechos mais específicos e
    relevantes para a pergunta do usuário.
    """

    query_emb = _text_embedding(query)

    emb_dir = os.path.join(base_dir, VECTOR_DIR_NAME)
    chunk_vec_file = os.path.join(emb_dir, RAW_CHUNK_VECTOR_FILE)
    chunk_vecs = _load_json(chunk_vec_file, [])
    if not chunk_vecs:
        return []

    # Mapa id -> info do chunk para rápido acesso
    chunk_by_id = {c["id"]: c for c in chunk_vecs}

    if _HAVE_FAISS and os.path.exists(os.path.join(emb_dir, RAW_CHUNK_FAISS_FILE)):
        top_ids = _faiss_search(base_dir, RAW_CHUNK_FAISS_FILE, query_emb, top_n)
    else:
        scores = []
        for ch in chunk_vecs:
            sim = _cosine_similarity(query_emb, ch.get("embedding", []))
            scores.append((sim, ch["id"]))
        scores.sort(reverse=True)
        top_ids = [cid for _, cid in scores[:top_n]]

    trechos = []
    usados = set()
    for cid in top_ids:
        chunk = chunk_by_id.get(cid)
        if not chunk:
            continue
        raw_id = chunk.get("raw_id")
        if raw_id in usados:
            continue
        usados.add(raw_id)
        msgs = _ler_raw_intervalo(base_dir, raw_id, raw_id)
        role = msgs[0]["role"] if msgs else "user"
        prefix = "Usuário" if role == "user" else "IA"
        trechos.append(f"{prefix}: {chunk['text']}")
    return trechos

def carregar_memoria(arquivo=DEFAULT_MEMORY_FILE):
    """Carrega o dicionário de memória persistido em *arquivo*.

    Caso o arquivo não exista ou contém dados inválidos, retorna uma
    estrutura padrão em formato de dicionário. Isso evita erros quando, por
    algum motivo, o JSON salvo ficou corrompido ou possui um formato
    inesperado (por exemplo uma lista vazia), o que levou ao
    ``AttributeError`` relatado.
    """

    memoria = {}
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                memoria = json.load(f)
        except Exception:
            # Arquivo corrompido ou não é JSON válido
            memoria = {}

    if not isinstance(memoria, dict):
        memoria = {}
    
    memoria.setdefault("usuario", {})
    memoria.setdefault("personagem", {})
    memoria.setdefault("conversa", [])
    memoria.setdefault("resumo_breve", [])
    memoria.setdefault("contador_interacoes", 0)

    # Limita o tamanho das listas de resumos para evitar crescimento indefinido
    memoria["resumo_breve"] = memoria.get("resumo_breve", [])[-MAX_RESUMOS:]

    return memoria

def salvar_memoria(memoria, arquivo=DEFAULT_MEMORY_FILE):
    os.makedirs(os.path.dirname(arquivo), exist_ok=True)
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(memoria, f, indent=2, ensure_ascii=False)


def _load_json(path, default):
    """Load JSON data from *path* returning *default* on error."""
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default


def _save_json(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _append_jsonl(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
        f.write("\n")


def _load_meta(base_dir):
    """Load or initialize metadata for hierarchical memory."""
    meta = _load_json(os.path.join(base_dir, "meta.json"), {})
    if not isinstance(meta, dict):
        meta = {}
    meta.setdefault("current_raw", 1)
    meta.setdefault("count_in_raw", 0)
    meta.setdefault("last_id", 0)
    return meta


def _save_meta(meta, base_dir):
    _save_json(meta, os.path.join(base_dir, "meta.json"))


def init_hierarchical(base_dir):
    os.makedirs(os.path.join(base_dir, "raw"), exist_ok=True)
    for fname in ["episodic_summaries.json", "historical_summaries.json", "global_summary.json"]:
        path = os.path.join(base_dir, fname)
        if not os.path.exists(path):
            _save_json([], path)
    if not os.path.exists(os.path.join(base_dir, "meta.json")):
        _save_meta({"current_raw": 1, "count_in_raw": 0, "last_id": 0}, base_dir)
    init_vector_store(base_dir)
    # create empty vector files
    for fname in [EPISODIC_VECTOR_FILE, RAW_VECTOR_FILE, RAW_CHUNK_VECTOR_FILE]:
        path = os.path.join(base_dir, VECTOR_DIR_NAME, fname)
        if not os.path.exists(path):
            _save_json([], path)


def resetar_memoria_personagem(nome):
    """Apaga e recria todos os arquivos de memória do *nome* informado."""
    base = os.path.join(DEFAULT_MEMORY_DIR, nome)
    if os.path.exists(base):
        shutil.rmtree(base)
    init_hierarchical(base)
    caminho = os.path.join(base, "working_memory.json")
    memoria = carregar_memoria(caminho)
    salvar_memoria(memoria, caminho)


def registrar_raw(role, content, base_dir):
    meta = _load_meta(base_dir)
    msg_id = meta["last_id"] + 1
    raw_file = os.path.join(base_dir, "raw", f"raw_{meta['current_raw']}.jsonl")
    _append_jsonl(raw_file, {"id": msg_id, "role": role, "content": content})
    add_raw_embedding(base_dir, msg_id, content)
    add_raw_chunk_embeddings(base_dir, msg_id, content)
    meta["last_id"] = msg_id
    meta["count_in_raw"] += 1
    if meta["count_in_raw"] >= RAW_ROTATE:
        meta["current_raw"] += 1
        meta["count_in_raw"] = 0
    _save_meta(meta, base_dir)
    return msg_id


def remover_ultimas_raw(base_dir, n=1):
    """Remove as *n* últimas mensagens registradas nos arquivos raw."""
    meta = _load_meta(base_dir)
    while n > 0 and meta["last_id"] > 0:
        raw_file = os.path.join(base_dir, "raw", f"raw_{meta['current_raw']}.jsonl")
        if not os.path.exists(raw_file):
            if meta["current_raw"] > 1:
                meta["current_raw"] -= 1
                continue
            break

        with open(raw_file, "r+", encoding="utf-8") as f:
            linhas = f.readlines()
            if not linhas:
                f.truncate(0)
                if meta["current_raw"] > 1:
                    meta["current_raw"] -= 1
                meta["count_in_raw"] = 0
                continue
            linhas.pop()
            f.seek(0)
            f.truncate()
            f.writelines(linhas)

        meta["last_id"] -= 1
        meta["count_in_raw"] -= 1
        n -= 1

        if meta["count_in_raw"] == 0 and meta["current_raw"] > 1:
            meta["current_raw"] -= 1
            prev_file = os.path.join(base_dir, "raw", f"raw_{meta['current_raw']}.jsonl")
            if os.path.exists(prev_file):
                with open(prev_file, "r", encoding="utf-8") as pf:
                    meta["count_in_raw"] = len(pf.readlines())
            else:
                meta["count_in_raw"] = 0

    _save_meta(meta, base_dir)
    rebuild_raw_embeddings(base_dir)


def _ler_raw_intervalo(base_dir, start_id, end_id):
    meta = _load_meta(base_dir)
    mensagens = []
    for idx in range(1, meta["current_raw"] + 1):
        arq = os.path.join(base_dir, "raw", f"raw_{idx}.jsonl")
        if not os.path.exists(arq):
            continue
        with open(arq, "r", encoding="utf-8") as f:
            for linha in f:
                if not linha.strip():
                    continue
                msg = json.loads(linha)
                if msg["id"] < start_id:
                    continue
                mensagens.append(msg)
                if msg["id"] >= end_id:
                    return mensagens
    return mensagens


def _save_episodic_summary(base_dir, start_id, end_id, resumo):
    arquivo = os.path.join(base_dir, "episodic_summaries.json")
    episodios = _load_json(arquivo, [])
    new_id = len(episodios) + 1
    episodios.append({
        "id": new_id,
        "start_id": start_id,
        "end_id": end_id,
        "summary": resumo,
    })
    _save_json(episodios, arquivo)
    return new_id


def _save_branch_summary(base_dir, episodic_ids, resumo):
    arquivo = os.path.join(base_dir, "historical_summaries.json")
    branches = _load_json(arquivo, [])
    new_id = len(branches) + 1
    branches.append({
        "id": new_id,
        "episodic_ids": episodic_ids,
        "summary": resumo,
    })
    _save_json(branches, arquivo)
    return new_id


def _save_global_summary(base_dir, branch_ids, resumo):
    arquivo = os.path.join(base_dir, "global_summary.json")
    globais = _load_json(arquivo, [])
    globais.append({
        "id": len(globais) + 1,
        "branch_ids": branch_ids,
        "summary": resumo,
    })
    _save_json(globais, arquivo)


def gerar_resumo_episodio(base_dir, resumo_func):
    meta = _load_meta(base_dir)
    if meta["last_id"] % EPISODE_SIZE != 0:
        return None
    start_id = meta["last_id"] - EPISODE_SIZE + 1
    mensagens = _ler_raw_intervalo(base_dir, start_id, meta["last_id"])
    trechos = [f"{'Usuário' if m['role']=='user' else 'IA'}: {m['content']}" for m in mensagens]
    resumo = resumo_func(trechos)
    eid = _save_episodic_summary(base_dir, start_id, meta["last_id"], resumo)
    add_episodic_embedding(base_dir, eid, resumo)
    return resumo


def gerar_resumo_branch(base_dir, resumo_func):
    episodios = _load_json(os.path.join(base_dir, "episodic_summaries.json"), [])
    branches = _load_json(os.path.join(base_dir, "historical_summaries.json"), [])
    if len(episodios) < EPISODES_PER_BRANCH * (len(branches) + 1):
        return None
    start = len(branches) * EPISODES_PER_BRANCH
    subset = episodios[start:start + EPISODES_PER_BRANCH]
    trechos = [e["summary"] for e in subset]
    resumo = resumo_func(trechos)
    _save_branch_summary(base_dir, [e["id"] for e in subset], resumo)
    rebuild_historical_embeddings(base_dir)
    rebuild_episodic_embeddings(base_dir)
    return resumo


def gerar_resumo_global(base_dir, resumo_func):
    branches = _load_json(os.path.join(base_dir, "historical_summaries.json"), [])
    globais = _load_json(os.path.join(base_dir, "global_summary.json"), [])
    if len(branches) < BRANCHES_PER_GLOBAL * (len(globais) + 1):
        return None
    start = len(globais) * BRANCHES_PER_GLOBAL
    subset = branches[start:start + BRANCHES_PER_GLOBAL]

    valid = []
    for item in subset:
        if isinstance(item, dict) and "id" in item and "summary" in item:
            valid.append(item)
        else:
            warnings.warn(
                "Ignorando entrada inválida em historical_summaries.json",
                RuntimeWarning,
            )
    if len(valid) < BRANCHES_PER_GLOBAL:
        return None

    trechos = [b["summary"] for b in valid]
    resumo = resumo_func(trechos)
    _save_global_summary(base_dir, [b["id"] for b in valid], resumo)
    return resumo
