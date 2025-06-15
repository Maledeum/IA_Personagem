# memoria.py
import json
import os
import warnings
import shutil
import hashlib

DEFAULT_MEMORY_DIR = "memory"
DEFAULT_MEMORY_FILE = os.path.join(DEFAULT_MEMORY_DIR, "working_memory.json")

RAW_ROTATE = 500  # mensagens por arquivo raw
EPISODE_SIZE = 10
EPISODES_PER_BRANCH = 4
BRANCHES_PER_GLOBAL = 4
VECTOR_DIR_NAME = "vectors"
EPISODIC_VECTOR_FILE = "episodic_vectors.json"
HISTORICAL_VECTOR_FILE = "historical_vectors.json"
MAX_RESUMOS = 5


def _text_embedding(text, size=32):
    """Return a deterministic embedding list for *text*."""
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return [b / 255 for b in digest[:size]]


def init_vector_store(base_dir):
    """Ensure the vector directory exists for this personality."""
    path = os.path.join(base_dir, VECTOR_DIR_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def add_episodic_embedding(base_dir, episodic_id, resumo):
    """Append embedding for a new episodic summary."""
    emb_dir = init_vector_store(base_dir)
    file_path = os.path.join(emb_dir, EPISODIC_VECTOR_FILE)
    data = _load_json(file_path, [])
    data.append({"id": episodic_id, "embedding": _text_embedding(resumo)})
    _save_json(data, file_path)


def rebuild_episodic_embeddings(base_dir):
    """Recalculate embeddings for all episodic summaries."""
    emb_dir = init_vector_store(base_dir)
    file_path = os.path.join(emb_dir, EPISODIC_VECTOR_FILE)
    episodios = _load_json(os.path.join(base_dir, "episodic_summaries.json"), [])
    data = [{"id": e["id"], "embedding": _text_embedding(e["summary"])} for e in episodios]
    _save_json(data, file_path)


def rebuild_historical_embeddings(base_dir):
    """Recalculate embeddings for all historical summaries."""
    emb_dir = init_vector_store(base_dir)
    file_path = os.path.join(emb_dir, HISTORICAL_VECTOR_FILE)
    historicos = _load_json(os.path.join(base_dir, "historical_summaries.json"), [])
    data = [{"id": h["id"], "embedding": _text_embedding(h["summary"])} for h in historicos]
    _save_json(data, file_path)


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


def buscar_trechos(query, base_dir, top_n=3):
    """Retorna os *top_n* trechos mais similares ao *query*."""
    query_emb = _text_embedding(query)

    vec_file = os.path.join(base_dir, VECTOR_DIR_NAME, EPISODIC_VECTOR_FILE)
    episodic_vecs = _load_json(vec_file, [])
    if not episodic_vecs:
        return []

    scores = []
    for item in episodic_vecs:
        sim = _cosine_similarity(query_emb, item.get("embedding", []))
        scores.append((sim, item["id"]))
    scores.sort(reverse=True)
    top_ids = [eid for _, eid in scores[:top_n]]

    episodios = _load_json(os.path.join(base_dir, "episodic_summaries.json"), [])
    id_range = {e["id"]: (e["start_id"], e["end_id"]) for e in episodios}

    trechos = []
    for eid in top_ids:
        if eid not in id_range:
            continue
        start_id, end_id = id_range[eid]
        mensagens = _ler_raw_intervalo(base_dir, start_id, end_id)
        trecho = "\n".join(
            f"{'Usuário' if m['role']=='user' else 'IA'}: {m['content']}" for m in mensagens
        )
        trechos.append(trecho)
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
    memoria.setdefault("resumo_antigo", [])
    memoria.setdefault("contador_interacoes", 0)

    # Limita o tamanho das listas de resumos para evitar crescimento indefinido
    memoria["resumo_breve"] = memoria.get("resumo_breve", [])[-MAX_RESUMOS:]
    memoria["resumo_antigo"] = memoria.get("resumo_antigo", [])[-MAX_RESUMOS:]

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
