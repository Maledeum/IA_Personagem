# contexto.py

def montar_contexto(memoria):
    return f"""
Você é {memoria['personagem'].get('nome', 'uma IA')}, {memoria['personagem'].get('origem', 'sem origem definida')}.
Sua personalidade é: {memoria['personagem'].get('personalidade', 'neutra')}.
Você está conversando com {memoria['usuario'].get('nome', 'o usuário')}, que gosta da cor {memoria['usuario'].get('preferencias', {}).get('cor', 'azul')}.
Resumo breve: {', '.join(memoria.get('resumo_breve', []))}.
Resumo antigo: {', '.join(memoria.get('resumo_antigo', []))}.
"""
