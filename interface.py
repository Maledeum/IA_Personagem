import gradio as gr
import os
import json
import time
import psutil
from core.chat import (
    conversar,
    set_system_prompt,
    set_memory_file,
    memoria,
    memory_file,
)
from core.memoria import carregar_memoria, salvar_memoria
from transformers import GPT2TokenizerFast
tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")

PERSONALIDADES_DIR = "personalidades"

def carregar_personalidades():
    personalidades = {}
    for arq in os.listdir(PERSONALIDADES_DIR):
        if arq.endswith(".json"):
            caminho = os.path.join(PERSONALIDADES_DIR, arq)
            with open(caminho, "r", encoding="utf-8") as f:
                dados = json.load(f)
            nome = dados.get("nome", os.path.splitext(arq)[0])
            personalidades[nome] = {
                "dados": dados,
                "arquivo": caminho,
                "id": os.path.splitext(arq)[0],
            }
    return personalidades

PERSONALIDADES = carregar_personalidades()
PERSONALIDADE_PADRAO = list(PERSONALIDADES.keys())[0]

def inicializar_personalidade(nome):
    info = PERSONALIDADES[nome]
    set_system_prompt(info["dados"].get("prompt", ""))
    caminho_mem = os.path.join("memory", f"{info['id']}.json")
    set_memory_file(caminho_mem)
    global memoria
    memoria = carregar_memoria(caminho_mem)

inicializar_personalidade(PERSONALIDADE_PADRAO)

def responder(pergunta, historico):
    resposta_acumulada = ""
    historico.append({"role": "user", "content": pergunta})
    historico.append({"role": "assistant", "content": ""})  # placeholder
    
    start_time = time.time()
    process = psutil.Process()

    token_count = 0
    buffer = ""

    for token in conversar(pergunta):
        buffer += token
        token_count += 1  # contar token gerado (simplificado)

        # Yield a cada 20 caracteres ou ao encontrar pontuação para UI não travar
        if len(buffer) > 20 or token.endswith(('.', '!', '?')):
            resposta_acumulada += buffer
            historico[-1]["content"] = resposta_acumulada
            yield historico, historico, "", ""  # mantém os 4 outputs
            buffer = ""

    # Se sobrou buffer, envia o resto
    if buffer:
        resposta_acumulada += buffer
        historico[-1]["content"] = resposta_acumulada
        yield historico, historico, "", ""

    elapsed_time = time.time() - start_time
    avg_time_per_token = elapsed_time / max(token_count, 1)
    ram_usage_mb = process.memory_info().rss / 1024 / 1024

    metricas = (
        f"⏱ Tempo total: {elapsed_time:.2f}s\n"
        f"🧠 Tokens: {token_count}\n"
        f"📊 Tempo médio/token: {avg_time_per_token:.4f}s\n"
        f"💾 RAM: {ram_usage_mb:.1f} MB"
    )

    # Última yield com métricas e input limpo
    yield historico, historico, metricas, ""

def carregar_historico():
    conversa = memoria.get("conversa", [])
    historico = []
    for msg in conversa:
        if msg["role"] in ["user", "assistant"]:
            historico.append({"role": msg["role"], "content": msg["content"]})
    return historico, historico

def escolher_personalidade(nome):
    inicializar_personalidade(nome)
    return carregar_historico()

def excluir_ultima_interacao(historico):
    if len(historico) >= 2:
        del historico[-2:]
        if memoria.get("conversa"):
            memoria["conversa"] = memoria["conversa"][:-2]
            salvar_memoria(memoria, memory_file)
    return historico, historico

chatbot = gr.Chatbot(label="Assistente IA", type="messages")
entrada = gr.Textbox(placeholder="Digite sua pergunta...", label="Você:")
estado = gr.State([])
botao_carregar = gr.Button("🔄 Carregar histórico")
botao_excluir = gr.Button("🗑️ Excluir última mensagem")
seletor = gr.Dropdown(list(PERSONALIDADES.keys()), label="Personalidade", value=PERSONALIDADE_PADRAO)
metricas = gr.Textbox(label="Métricas de desempenho", interactive=False, lines=4)

with gr.Blocks(title="IA com Memória") as demo:
    gr.Markdown("## Assistente IA com múltiplas personalidades")
    gr.Markdown("Construído com LM Studio + Gradio")
    
    seletor.render()
    chatbot.render()
    entrada.render()
    
    with gr.Row():
        botao_carregar.render()
        botao_excluir.render()
    
    estado.render()
    metricas.render()

    entrada.submit(fn=responder, inputs=[entrada, estado], outputs=[chatbot, estado, metricas, entrada])
    botao_carregar.click(fn=carregar_historico, inputs=[], outputs=[chatbot, estado])
    botao_excluir.click(fn=excluir_ultima_interacao, inputs=estado, outputs=[chatbot, estado])
    seletor.change(fn=escolher_personalidade, inputs=seletor, outputs=[chatbot, estado])

if __name__ == "__main__":
    demo.launch()



