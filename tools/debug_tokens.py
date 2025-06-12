import json
import sys
from transformers import GPT2TokenizerFast

# Caminho para o arquivo de memória padrão
MEMORY_FILE = "memory/default/working_memory.json"

def contar_tokens_mensagens(mensagens):
    tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
    return sum(len(tokenizer.encode(m["content"])) for m in mensagens)

def main(mem_file=MEMORY_FILE):
    try:
        with open(mem_file, "r", encoding="utf-8") as f:
            memoria = json.load(f)
    except FileNotFoundError:
        print(f"Arquivo {mem_file} não encontrado.")
        return

    conversa = memoria.get("conversa", [])
    tokens_usados = contar_tokens_mensagens(conversa)
    print(f"Tokens usados na conversa: {tokens_usados}")

    # Também dá para mostrar o número de mensagens
    print(f"Número de mensagens na conversa: {len(conversa)}")

if __name__ == "__main__":
    caminho = sys.argv[1] if len(sys.argv) > 1 else MEMORY_FILE
    main(caminho)
