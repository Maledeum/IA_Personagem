# contexto.py

def montar_contexto(memoria):
    """Monta o contexto do prompt a partir da memória carregada."""

    personagem = memoria.get("personagem", {})
    usuario = memoria.get("usuario", {})

    linhas = [
        f"Você é {personagem.get('nome', 'uma IA')}, {personagem.get('origem', 'sem origem definida')}.",
        f"Sua personalidade é: {personagem.get('personalidade', 'neutra')}.",
    ]

    if "idade" in personagem:
        linhas.append(f"Idade: {personagem['idade']}.")
    if "aparencia" in personagem:
        linhas.append(f"Aparência: {personagem['aparencia']}")
    if "modo_falar" in personagem:
        linhas.append(f"Modo de falar: {personagem['modo_falar']}.")
    if "relacoes" in personagem and isinstance(personagem["relacoes"], dict):
        rel = ', '.join(f"{k}: {v}" for k, v in personagem["relacoes"].items())
        linhas.append(f"Relações: {rel}.")
    if "inventario" in personagem:
        itens = ', '.join(personagem["inventario"])
        linhas.append(f"Inventário: {itens}.")

    linhas.append(
        f"Você está conversando com {usuario.get('nome', 'o usuário')}, que gosta da cor {usuario.get('preferencias', {}).get('cor', 'azul')}.")
    if "idade" in usuario:
        linhas.append(f"Idade do usuário: {usuario['idade']}.")
    if "modo_falar" in usuario:
        linhas.append(f"Usuário fala de forma {usuario['modo_falar']}.")
    linhas.append(f"Resumo breve: {', '.join(memoria.get('resumo_breve', []))}.")
    linhas.append(f"Resumo antigo: {', '.join(memoria.get('resumo_antigo', []))}.")

    return "\n".join(linhas)
