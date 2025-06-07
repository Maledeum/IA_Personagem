import time
import requests
import json

payload = {
    "model": "local-model",
    "messages": [{"role": "user", "content": "Olá, teste rápido para medir performance."}],
    "temperature": 0.7,
    "max_tokens": 100,
    "stream": False
}

start = time.time()
response = requests.post("http://localhost:1234/v1/chat/completions", json=payload)
elapsed = time.time() - start

print(f"Tempo total (100 tokens, sem stream): {elapsed:.2f} segundos")
print(response.json())
