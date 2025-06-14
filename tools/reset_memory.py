import sys
from core.memoria import resetar_memoria_personagem

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python tools/reset_memory.py <nome_personagem>")
    else:
        personagem = sys.argv[1]
        resetar_memoria_personagem(personagem)
        print(f"Memória de '{personagem}' reiniciada.")

