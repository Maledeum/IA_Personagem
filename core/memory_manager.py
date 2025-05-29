import os
import json
from datetime import datetime

class MemoryManager:
    """
    Gerencia a memória de um único personagem, com:
    - raw_history.json: histórico completo (folhas brutas + contador)
    - working_memory.json: últimas N interações (folhas)
    """
    def __init__(
        self,
        character_name: str,
        base_dir: str = "memory",
        working_size: int = 20,
    ):
        self.character = character_name
        # directory: memory/<character_name>/
        self.dir = os.path.join(base_dir, character_name)
        os.makedirs(self.dir, exist_ok=True)

        self.raw_path = os.path.join(self.dir, "raw_history.json")
        self.working_path = os.path.join(self.dir, "working_memory.json")
        self.working_size = working_size
        self._ensure_files()

    def _ensure_files(self):
        # cria raw_history.json
        if not os.path.exists(self.raw_path):
            with open(self.raw_path, 'w', encoding='utf-8') as f:
                json.dump({"counter": 0, "history": []}, f, ensure_ascii=False, indent=2)
        # cria working_memory.json
        if not os.path.exists(self.working_path):
            with open(self.working_path, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)

    def record_interaction(self, role: str, content: str, timestamp: datetime = None):
        """
        Adiciona uma nova interação:
        1) raw_history: append e incrementa counter
        2) working_memory: mantém apenas últimas N interações
        """
        ts = (timestamp or datetime.utcnow()).isoformat()
        # 1) atualizar raw
        with open(self.raw_path, 'r+', encoding='utf-8') as f:
            data = json.load(f)
            entry = {"speaker": role, "text": content, "timestamp": ts}
            data['history'].append(entry)
            data['counter'] += 1
            f.seek(0)
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.truncate()
        # 2) atualizar working
        recent = data['history'][-self.working_size:]
        with open(self.working_path, 'w', encoding='utf-8') as f:
            json.dump(recent, f, ensure_ascii=False, indent=2)

    def get_recent(self, n: int = None) -> list:
        """
        Retorna as últimas n interações (ou self.working_size se None).
        Cada item é um dict {speaker, text, timestamp}.
        """
        n = n or self.working_size
        with open(self.working_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data[-n:]

    def get_all(self) -> list:
        """
        Retorna todo o histórico bruto (lista de entradas).
        """
        with open(self.raw_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['history']