# IA_Personagem

Aria é uma assistente de IA projetada para manter memórias hierárquicas das interações com o usuário. A aplicação utiliza um modelo local compatível com a API do OpenAI e registra resumos periódicos para melhorar o contexto de longo prazo.

## Configuração do ambiente

1. Tenha o Python 3.10+ instalado.
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Opcionalmente defina a variável `LM_API_URL` apontando para o endpoint de chat do seu modelo local (por padrão `http://localhost:1234/v1/chat/completions`).

O diretório `memory/` é criado automaticamente pelo `MemoryManager` para armazenar o histórico e resumos.

## Como executar

### Linha de comando

```bash
python main.py
```
Inicia uma conversa simples no terminal com Aria.

### Interface web

```bash
python interface.py
```
Abre uma interface do Gradio em seu navegador para conversar com Aria e visualizar métricas básicas de desempenho.

## Ferramentas opcionais

O diretório `tools/` contém scripts auxiliares para depuração e testes:

- `debug_tokens.py` – conta tokens e mensagens armazenados no arquivo de memória.
- `performance_test.py` – faz checagens rápidas no arquivo de memória e simula tempos de resposta.
- `teste local.py` – exemplo de requisição direta ao endpoint local para medir desempenho.

Essas ferramentas não são necessárias para o uso normal, mas podem ajudar a analisar o comportamento do sistema.
