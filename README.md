# IA_Personagem

IA_Personagem é uma plataforma de chat em que cada personagem é uma IA com personalidade própria. O sistema mantém memória hierárquica da conversa e pode ser utilizado via terminal ou interface web (Gradio).

## Requisitos

- Python 3.10+
- Dependências: `requests`, `gradio`, `psutil`, `transformers`

Instale as dependências com:

```bash
pip install -r requirements.txt
```

## Estrutura

- `core/` – módulos principais de chat, memória e contexto
- `personalidades/` – arquivos JSON com as personalidades disponíveis
- `interface.py` – versão com interface web (Gradio)
- `main.py` – versão para uso no terminal
- `tools/` – scripts auxiliares para depuração e testes (inclui `reset_memory.py` para limpar a memória de um personagem)

O arquivo de memória agora é salvo em `memory/<personagem>.json` e será criado automaticamente na primeira execução de cada personalidade.

## Executando

### Terminal

```bash
python main.py nome_da_personalidade
```
Substitua `nome_da_personalidade` pelo arquivo desejado em `personalidades/` (ex.: `aria` ou `beto`).

### Interface Web

```bash
python interface.py
```

A aplicação abrirá um servidor local com chat em tempo real.

### Resetar memória

Para apagar todos os arquivos de memória de um personagem e começar do zero:

```bash
python tools/reset_memory.py nome_da_personalidade
```


## Verificação Rápida

Para verificar a integridade do código Python:

```bash
python -m py_compile interface.py main.py core/chat.py core/memoria.py core/contexto.py core/resumo.py tools/debug_tokens.py tools/performance_test.py "tools/teste local.py"
```

Os scripts em `tools/` dependem da biblioteca `transformers` para calcular tokens. Caso ela não esteja instalada, esses scripts exibirão um erro.

