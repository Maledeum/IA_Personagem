import os
import sys
from core.chat import conversar, carregar_personalidade, carregar_usuario

PERSONALIDADES_DIR = "personalidades"
USUARIOS_DIR = "usuarios"

def carregar_personalidade_cli(nome):
    """Carrega a personalidade *nome* utilizando chat.carregar_personalidade."""
    caminho = os.path.join(PERSONALIDADES_DIR, f"{nome}.json")
    return carregar_personalidade(caminho)

def carregar_usuario_cli(nome):
    """Carrega o perfil de usuário *nome* utilizando chat.carregar_usuario."""
    caminho = os.path.join(USUARIOS_DIR, f"{nome}.json")
    if os.path.exists(caminho):
        carregar_usuario(caminho)
        return True
    return False

if __name__ == "__main__":
    nome_persona = sys.argv[1] if len(sys.argv) > 1 else "aria"
    nome_exibicao = carregar_personalidade_cli(nome_persona)
    nome_usuario = sys.argv[2] if len(sys.argv) > 2 else "padrao"
    carregar_usuario_cli(nome_usuario)
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


