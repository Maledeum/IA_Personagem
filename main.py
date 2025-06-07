import os
import json
import sys
from core.chat import conversar, set_system_prompt, set_memory_file

PERSONALIDADES_DIR = "personalidades"

def carregar_personalidade(nome):
    caminho = os.path.join(PERSONALIDADES_DIR, f"{nome}.json")
    with open(caminho, "r", encoding="utf-8") as f:
        dados = json.load(f)
    set_system_prompt(dados.get("prompt", ""))
    set_memory_file(os.path.join("memory", nome))
    return dados.get("nome", nome)

if __name__ == "__main__":
    nome_persona = sys.argv[1] if len(sys.argv) > 1 else "aria"
    nome_exibicao = carregar_personalidade(nome_persona)
    print(f"🧠 {nome_exibicao} está pronta para conversar.\n")

    while True:
        entrada = input("Você: ")
        if entrada.lower() in ["sair", "exit", "quit"]:
            break

        resposta = ""
        for token in conversar(entrada):
            print(token, end="", flush=True)
            resposta += token
        print("\n")


