import gradio as gr
from core.chat import conversar
from core.memoria import carregar_memoria
import time
import psutil
from transformers import GPT2TokenizerFast
tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
memoria = carregar_memoria()

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

chatbot = gr.Chatbot(label="Aria - Assistente IA", type="messages")
entrada = gr.Textbox(placeholder="Digite sua pergunta...", label="Você:")
estado = gr.State([])
botao_carregar = gr.Button("🔄 Carregar histórico")
metricas = gr.Textbox(label="Métricas de desempenho", interactive=False, lines=4)

with gr.Blocks(title="Aria - IA com Memória") as demo:
    gr.Markdown("## Aria - Assistente IA com memória em camadas")
    gr.Markdown("Construído com LM Studio + Gradio")

    chatbot.render()
    entrada.render()
    botao_carregar.render()
    estado.render()
    metricas.render()

    entrada.submit(fn=responder, inputs=[entrada, estado], outputs=[chatbot, estado, metricas, entrada])
    botao_carregar.click(fn=carregar_historico, inputs=[], outputs=[chatbot, estado])

if __name__ == "__main__":
    demo.launch()



