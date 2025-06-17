"""Funções utilitárias para organizar o contexto enviado ao modelo."""

from typing import List, Dict


def _montar_resumos(memoria: dict) -> List[Dict[str, str]]:
    """Retorna até três mensagens de resumo em ordem mais recente."""
    resumos = memoria.get("resumo_breve", [])[-3:]
    mensagens = []
    for resumo in resumos:
        mensagens.append({"role": "system", "content": f"Resumo breve: {resumo}"})
    return mensagens


def _montar_interacoes(memoria: dict, n: int = 4) -> List[Dict[str, str]]:
    """Retorna as últimas *n* mensagens do chat mantendo seus roles."""
    interacoes = memoria.get("conversa", [])[-n:]
    return list(interacoes)


def montar_prompt(system_prompt: str, pergunta: str, memoria: dict, rag_trechos: List[str] | None = None) -> List[Dict[str, str]]:
    """Monta a lista final de mensagens para o modelo."""

    mensagens: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]

    mensagens.extend(_montar_resumos(memoria))
    mensagens.extend(_montar_interacoes(memoria))

    if rag_trechos:
        texto = "\n----\n".join(rag_trechos)
        mensagens.append({"role": "system", "content": "Trechos relevantes:\n" + texto})

    mensagens.append({"role": "user", "content": pergunta})
    return mensagens

