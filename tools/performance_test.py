import json
import os
import sys
import time
from transformers import GPT2TokenizerFast

# Caminho para o arquivo de memória padrão
MEMORY_FILE = "memory/default/working_memory.json"

def contar_tokens_mensagens(mensagens):
    try:
        tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
    except Exception as e:
        print("Erro ao carregar tokenizer GPT-2:", e)
        return 0
    return sum(len(tokenizer.encode(m["content"])) for m in mensagens if m.get("content"))

def testar_memoria(mem_file=MEMORY_FILE):
    print("\n[TESTE] Verificando arquivo de memória...")
    if not os.path.exists(mem_file):
        print("❌ Arquivo de memória não existe.")
        return None
    try:
        with open(mem_file, "r", encoding="utf-8") as f:
            dados = json.load(f)
        assert "conversa" in dados
        assert isinstance(dados["conversa"], list)
        print("✅ Memória válida e acessível.")
        return dados["conversa"]
    except Exception as e:
        print(f"❌ Erro ao carregar ou validar memória: {e}")
        return None

def verificar_mensagens_vazias(conversa):
    print("\n[TESTE] Verificando mensagens vazias...")
    vazias = [i for i, m in enumerate(conversa) if not m.get("content")]
    if vazias:
        print(f"⚠️ {len(vazias)} mensagens vazias encontradas: índices {vazias}")
    else:
        print("✅ Nenhuma mensagem vazia encontrada.")

def contar_tokens(conversa):
    print("\n[TESTE] Contando tokens...")
    total = contar_tokens_mensagens(conversa)
    print(f"📊 Tokens usados na conversa: {total}")
    print(f"🗂️ Total de mensagens: {len(conversa)}")

def simular_tempo_resposta():
    print("\n[TESTE] Simulando tempo de resposta...")
    start = time.time()
    _ = "".join("token" for _ in range(10000))
    end = time.time()
    print(f"⏱️ Tempo simulado de processamento: {end - start:.4f} segundos")

def main(mem_file=MEMORY_FILE):
    conversa = testar_memoria(mem_file)
    if conversa is None:
        return
    verificar_mensagens_vazias(conversa)
    contar_tokens(conversa)
    simular_tempo_resposta()

if __name__ == "__main__":
    caminho = sys.argv[1] if len(sys.argv) > 1 else MEMORY_FILE
    main(caminho)
