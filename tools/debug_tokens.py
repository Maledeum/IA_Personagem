import json
from transformers import GPT2TokenizerFast

# Caminho para o arquivo de memória
MEMORY_FILE = "memory/memory.json"

def contar_tokens_mensagens(mensagens):
    tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
    return sum(len(tokenizer.encode(m["content"])) for m in mensagens)

def main():
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            memoria = json.load(f)
    except FileNotFoundError:
        print(f"Arquivo {MEMORY_FILE} não encontrado.")
        return

    conversa = memoria.get("conversa", [])
    tokens_usados = contar_tokens_mensagens(conversa)
    print(f"Tokens usados na conversa: {tokens_usados}")

    # Também dá para mostrar o número de mensagens
    print(f"Número de mensagens na conversa: {len(conversa)}")

if __name__ == "__main__":
    main()
