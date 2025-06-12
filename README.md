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
- `personalidades/` – arquivos JSON com as personalidades disponíveis. Cada
  arquivo pode conter campos extras como `idade`, `aparencia`, `modo_falar`,
  `relacoes` e `inventario` que são carregados para compor o prompt.
- `usuarios/` – perfis de usuário que podem ser carregados e editados pela interface
- `interface.py` – versão com interface web (Gradio)
- `main.py` – versão para uso no terminal
- `tools/` – scripts auxiliares para depuração e testes

Cada personalidade armazena sua memória em `memory/<personagem>/working_memory.json`, criado automaticamente na primeira execução.

## Executando

### Terminal

```bash
python main.py nome_da_personalidade [perfil_usuario]
```
Substitua `nome_da_personalidade` pelo arquivo em `personalidades/` (ex.: `aria` ou `beto`).
Se desejar, informe também um perfil de usuário existente em `usuarios/`.

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

