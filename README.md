# IA_Personagem

IA_Personagem é uma plataforma de chat em que cada personagem é uma IA com personalidade própria. O sistema mantém memória hierárquica da conversa e pode ser utilizado via terminal ou interface web (Gradio).

## Requisitos

- Python 3.10+
- Dependências: `requests`, `gradio`, `psutil`, `transformers`

Instale as dependências com:

```bash
pip install -r requirements.txt
```

> Se não houver um `requirements.txt`, instale manualmente:
> `pip install requests gradio psutil transformers`

## Estrutura

- `core/` – módulos principais de chat, memória e contexto
- `config/personality.txt` – prompt base da personagem
- `interface.py` – versão com interface web (Gradio)
- `main.py` – versão para uso no terminal
- `tools/` – scripts auxiliares para depuração e testes

O arquivo de memória é salvo em `memory/memory.json` e será criado automaticamente na primeira execução.

## Executando

### Terminal

```bash
python main.py
```

### Interface Web

```bash
python interface.py
```

A aplicação abrirá um servidor local com chat em tempo real.

## Verificação Rápida

Para verificar a integridade do código Python:

```bash
python -m py_compile interface.py main.py core/chat.py core/memoria.py core/contexto.py core/resumo.py tools/debug_tokens.py tools/performance_test.py "tools/teste local.py"
```

Os scripts em `tools/` dependem da biblioteca `transformers` para calcular tokens. Caso ela não esteja instalada, esses scripts exibirão um erro.

