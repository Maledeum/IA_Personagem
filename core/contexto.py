# contexto.py

def montar_contexto(memoria):
    return f"""
Você é {memoria['personagem'].get('nome', 'Sem nome')}, {memoria['personagem'].get('raça', 'uma IA')}, do genero {memoria['personagem'].get('genero', 'sem genero')}, {memoria['personagem'].get('origem', 'sem origem definida')}.
Sua personalidade é: {memoria['personagem'].get('personalidade', 'neutra')}.
Você está conversando com {memoria['usuario'].get('nome', 'o usuário')}.
Resumo breve: {', '.join(memoria.get('resumo_breve', []))}.
"""
