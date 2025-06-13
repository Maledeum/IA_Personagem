import gradio as gr
import os
import json
import time
import psutil
import core.chat as chat
from core.memoria import salvar_memoria, remover_ultimas_raw
from transformers import GPT2TokenizerFast
tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")

PERSONALIDADES_DIR = "personalidades"
USUARIOS_DIR = "usuarios"

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

def carregar_usuario_padrao():
    """Carrega dados padrão de usuário do arquivo usuarios/padrao.json."""
    caminho = os.path.join(USUARIOS_DIR, "padrao.json")
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)
        chat.carregar_usuario(caminho)
        return dados
    return {}

PERSONALIDADES = carregar_personalidades()
PERSONALIDADE_PADRAO = list(PERSONALIDADES.keys())[0]
USUARIO_PADRAO = carregar_usuario_padrao()

def inicializar_personalidade(nome):
    """Carrega a personalidade selecionada utilizando chat.carregar_personalidade."""
    info = PERSONALIDADES[nome]
    chat.carregar_personalidade(info["arquivo"])

inicializar_personalidade(PERSONALIDADE_PADRAO)
carregar_usuario_padrao()

def responder(pergunta, historico):
    resposta_acumulada = ""
    historico.append({"role": "user", "content": pergunta})
    historico.append({"role": "assistant", "content": ""})  # placeholder
    
    start_time = time.time()
    process = psutil.Process()

    token_count = 0
    buffer = ""

    for token in chat.conversar(pergunta):
        buffer += token
        token_count += 1  # contar token gerado (simplificado)

        # Yield a cada 20 caracteres ou ao encontrar pontuação para UI não travar
        if len(buffer) > 20 or token.endswith(('.', '!', '?')):
            resposta_acumulada += buffer
            historico[-1]["content"] = resposta_acumulada
            yield historico, historico, "", "", chat.ultima_memoria_rag
            buffer = ""

    # Se sobrou buffer, envia o resto
    if buffer:
        resposta_acumulada += buffer
        historico[-1]["content"] = resposta_acumulada
        yield historico, historico, "", "", chat.ultima_memoria_rag

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
    yield historico, historico, metricas, "", chat.ultima_memoria_rag

def carregar_historico():
    conversa = chat.memoria.get("conversa", [])
    historico = []
    for msg in conversa:
        if msg["role"] in ["user", "assistant"]:
            historico.append({"role": msg["role"], "content": msg["content"]})
    return historico, historico

def escolher_personalidade(nome):
    inicializar_personalidade(nome)
    carregar_usuario_padrao()
    return carregar_historico()

def excluir_ultima_interacao(historico):
    if len(historico) >= 2:
        del historico[-2:]
        if chat.memoria.get("conversa"):
            chat.memoria["conversa"] = chat.memoria["conversa"][:-2]
            remover_ultimas_raw(chat.memory_base, 2)
            salvar_memoria(chat.memoria, chat.memory_file)
    return historico, historico

def atualizar_usuario(nome, cor):
    chat.memoria.setdefault("usuario", {})
    if nome:
        chat.memoria["usuario"]["nome"] = nome
    if cor:
        prefs = chat.memoria["usuario"].setdefault("preferencias", {})
        prefs["cor"] = cor
    salvar_memoria(chat.memoria, chat.memory_file)
    return carregar_historico()

chatbot = gr.Chatbot(label="Assistente IA", type="messages")
entrada = gr.Textbox(placeholder="Digite sua pergunta...", label="Você:")
estado = gr.State([])
botao_carregar = gr.Button("🔄 Carregar histórico")
botao_excluir = gr.Button("🗑️ Excluir última mensagem")
seletor = gr.Dropdown(list(PERSONALIDADES.keys()), label="Personalidade", value=PERSONALIDADE_PADRAO)
usuario_nome = gr.Textbox(label="Seu nome", value=USUARIO_PADRAO.get("nome", ""))
usuario_cor = gr.Textbox(label="Cor favorita", value=USUARIO_PADRAO.get("preferencias", {}).get("cor", ""))
botao_usuario = gr.Button("Salvar usuário")
metricas = gr.Textbox(label="Métricas de desempenho", interactive=False, lines=4)
with gr.Accordion("Memória recuperada", open=False) as acc:
    rag_box = gr.Markdown()
    rag_box.render()

with gr.Blocks(title="IA com Memória") as demo:
    gr.Markdown("## Assistente IA com múltiplas personalidades")
    gr.Markdown("Construído com LM Studio + Gradio")

    seletor.render()
    with gr.Row():
        usuario_nome.render()
        usuario_cor.render()
        botao_usuario.render()
    chatbot.render()
    entrada.render()
    
    with gr.Row():
        botao_carregar.render()
        botao_excluir.render()
    
    estado.render()
    metricas.render()
    acc.render()

    entrada.submit(fn=responder, inputs=[entrada, estado], outputs=[chatbot, estado, metricas, entrada, rag_box])
    botao_carregar.click(fn=carregar_historico, inputs=[], outputs=[chatbot, estado])
    botao_excluir.click(fn=excluir_ultima_interacao, inputs=estado, outputs=[chatbot, estado])
    botao_usuario.click(fn=atualizar_usuario, inputs=[usuario_nome, usuario_cor], outputs=[chatbot, estado])
    seletor.change(fn=escolher_personalidade, inputs=seletor, outputs=[chatbot, estado])

if __name__ == "__main__":
    demo.launch()



