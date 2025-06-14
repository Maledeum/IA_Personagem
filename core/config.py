import os

# Endpoint do backend de modelo. Pode ser sobrescrito com a variável de ambiente
# LM_API_URL para apontar para outro serviço compatível com a API OpenAI.
LM_API_URL = os.getenv("LM_API_URL", "http://localhost:1234/v1/chat/completions")
EMBED_MODEL = "all-MiniLM-L6-v2"

