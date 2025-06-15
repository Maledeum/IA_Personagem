# memoria.py
import json
import os

DEFAULT_MEMORY_DIR = "memory"
DEFAULT_MEMORY_FILE = os.path.join(DEFAULT_MEMORY_DIR, "memory.json")

def carregar_memoria(arquivo=DEFAULT_MEMORY_FILE):
    if os.path.exists(arquivo):
        with open(arquivo, "r", encoding="utf-8") as f:
            memoria = json.load(f)
    else:
        memoria = {
            "usuario": {},
            "personagem": {},
            "conversa": [],
            "resumo_breve": [],
            "contador_interacoes": 0
        }

    # Garante que todas as chaves existam mesmo se o arquivo já existia
    memoria.setdefault("resumo_breve", [])
    memoria.setdefault("conversa", [])
    memoria.setdefault("contador_interacoes", 0)

    return memoria

def salvar_memoria(memoria, arquivo=DEFAULT_MEMORY_FILE):
    os.makedirs(os.path.dirname(arquivo), exist_ok=True)
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(memoria, f, indent=2, ensure_ascii=False)