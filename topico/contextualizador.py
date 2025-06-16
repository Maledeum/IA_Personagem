
def contextualizar_pergunta(pergunta: str, memoria: dict, incluir_origem: bool = False) -> str:
    """Adiciona os tópicos ativos à *pergunta* para enriquecer o contexto."""
    topicos_dict = memoria.get("topicos_ativos", {})
    if not topicos_dict:
        return pergunta

    topicos_formatados = []
    for t, info in topicos_dict.items():
        if incluir_origem:
            topicos_formatados.append(f"{t} (por {info['origem']})")
        else:
            topicos_formatados.append(t)

    topico_str = ", ".join(topicos_formatados)
    return f"[Tópicos: {topico_str}] {pergunta}"
