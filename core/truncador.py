"""Utilitários para truncar conversas conforme limite de tokens."""

from typing import List, Dict


def estimar_tokens(texto: str) -> int:
    """Estima de forma simples o número de tokens de *texto*.

    A heurística considera que cada token possui em média quatro caracteres.
    Essa aproximação é suficiente para limitar o tamanho das conversas sem
    depender de bibliotecas externas.
    """
    if not texto:
        return 0
    return max(1, len(texto) // 4)


def _contar_tokens_mensagens(mensagens: List[Dict[str, str]]) -> int:
    """Retorna o total estimado de tokens nas *mensagens*."""
    total = 0
    for msg in mensagens:
        total += estimar_tokens(msg.get("content", ""))
    return total


def limitar_mensagens_com_prompt(prompt: str, conversa: List[Dict[str, str]], pergunta: str, limite: int = 3000) -> List[Dict[str, str]]:
    """Monta lista de mensagens respeitando o *limite* de tokens.

    - ``prompt`` será enviado como a primeira mensagem do sistema.
    - ``conversa`` é a lista histórica de mensagens no formato ``{"role": ..., "content": ...}``.
    - ``pergunta`` é a pergunta atual do usuário.

    As mensagens mais antigas são descartadas até que o total estimado de tokens
    fique abaixo do ``limite``.
    """
    mensagens = [{"role": "system", "content": prompt}]
    historico = list(conversa)
    historico.append({"role": "user", "content": pergunta})

    while historico and _contar_tokens_mensagens(mensagens + historico) > limite:
        historico.pop(0)

    mensagens.extend(historico)
    return mensagens
