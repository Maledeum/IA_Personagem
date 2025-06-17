"""Utilitários para truncar conversas conforme limite de tokens."""

from typing import List, Dict, Tuple, Optional


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


def limitar_mensagens_com_prompt(
    prompt: str,
    conversa: List[Dict[str, str]],
    pergunta: str,
    limite: int = 3000,
    return_metrics: bool = False,
) -> Tuple[List[Dict[str, str]], Optional[Dict[str, int]]]:
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

    tokens_prompt = estimar_tokens(prompt)
    tokens_original = tokens_prompt + _contar_tokens_mensagens(historico)

    while historico and _contar_tokens_mensagens(mensagens + historico) > limite:
        historico.pop(0)

    mensagens.extend(historico)

    metrics = None
    if return_metrics:
        tokens_final = _contar_tokens_mensagens(mensagens)
        metrics = {
            "limite": limite,
            "tokens_prompt": tokens_prompt,
            "tokens_original": tokens_original,
            "tokens_final": tokens_final,
            "prompt_truncado": tokens_prompt > limite,
            "conversa_truncada": tokens_final < tokens_original,
        }
    return mensagens, metrics
