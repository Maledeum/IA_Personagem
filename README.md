# IA_Personagem

IA_Personagem é uma aplicação de chat com múltiplas personalidades e memória hierárquica. Cada personagem possui um prompt próprio e guarda o histórico das conversas para gerar resumos automáticos. O sistema funciona tanto via terminal quanto por uma interface web em Gradio.

## Principais funcionalidades

- **Personalidades customizadas** em `personalidades/*.json`.
- **Memória hierárquica** com arquivos brutos, resumos de episódios e históricos.
- **Armazenamento de embeddings** para busca de trechos relevantes (RAG).
- **Interface web** opcional com Gradio (`interface.py`).
- **Uso pelo terminal** através de `main.py`.
- **Scripts utilitários** em `tools/` para depuração e reset de memória.

## Como o código funciona

1. **Chat** (`core/chat.py`)
   - Monta o prompt combinando o prompt do sistema, resumos e histórico.
   - Envia as mensagens para um modelo em `http://localhost:1234/v1/chat/completions`.
   - Registra as respostas na memória e atualiza os resumos.
2. **Memória** (`core/memoria.py`)
   - Guarda mensagens brutas em arquivos `memory/<persona>/raw/`.
   - Cria resumos periódicos (episódios, branches e global).
   - Converte resumos e mensagens em embeddings determinísticos (opcionalmente com FAISS).
3. **Contexto e tópicos** (`core/contexto.py`, `topico/`)
   - Extrai tópicos recentes para enriquecer perguntas.
   - Constrói a lista de mensagens que será enviada ao modelo.
4. **Interfaces**
   - `main.py` executa o chat no terminal.
   - `interface.py` oferece uma interface web com histórico e ações de gerenciamento.

## Instalação

Requer Python 3.10+. Instale as dependências:

```bash
pip install -r requirements.txt
python -m nltk.downloader punkt stopwords
```

## Execução rápida

### Terminal

```bash
python main.py aria  # escolha a personalidade desejada
```

### Interface Web

```bash
python interface.py
```

### Resetar memória

```bash
python tools/reset_memory.py aria
```

## Verificação rápida

Para garantir que os arquivos Python estão corretos:

```bash
python -m py_compile interface.py main.py core/chat.py core/memoria.py core/contexto.py core/resumo.py tools/debug_tokens.py tools/performance_test.py tools/teste_local.py
```

