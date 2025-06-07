# memoria.py
import json
import os

MEMORY_FILE = "memory/memory.json"

def carregar_memoria():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            memoria = json.load(f)
    else:
        memoria = {
            "usuario": {},
            "personagem": {},
            "conversa": [],
            "resumo_breve": [],
            "resumo_antigo": [],
            "contador_interacoes": 0
        }

    # Garante que todas as chaves existam mesmo se o arquivo já existia
    memoria.setdefault("resumo_breve", [])
    memoria.setdefault("resumo_antigo", [])
    memoria.setdefault("conversa", [])
    memoria.setdefault("contador_interacoes", 0)

    return memoria

def salvar_memoria(memoria):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memoria, f, indent=2, ensure_ascii=False)
