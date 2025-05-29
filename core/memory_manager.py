import os
import json
from datetime import datetime
from core.resumo import gerar_resumo_com_ia

class MemoryManager:
    """
    Gerencia memória hierárquica segmentada para um personagem.
    Arquivos:
      - raw_n.json            (segmentos de mensagens)
      - working_memory.json    (últimas N mensagens)
      - episodic_summaries.json (resumos episódicos)
      - historical_summaries.json (resumos de grupos de episódios)
      - global_summary.json    (resumo global)
      - meta.json             (controle de segmentos e índices)

    Configurações:
      working_size: int
      episodic_size: int
      branch_size: int
      segment_size: int
    """
    def __init__(
        self,
        character_name: str,
        base_dir: str = "memory",
        working_size: int = 20,
        episodic_size: int = 10,
        branch_size: int = 4,
        segment_size: int = 500
    ):
        self.base_dir = os.path.join(base_dir, character_name)
        os.makedirs(self.base_dir, exist_ok=True)
        self.working_size = working_size
        self.episodic_size = episodic_size
        self.branch_size = branch_size
        self.segment_size = segment_size

        # Paths
        self.working_path = os.path.join(self.base_dir, 'working_memory.json')
        self.episodic_path = os.path.join(self.base_dir, 'episodic_summaries.json')
        self.historical_path = os.path.join(self.base_dir, 'historical_summaries.json')
        self.global_path = os.path.join(self.base_dir, 'global_summary.json')
        self.meta_path = os.path.join(self.base_dir, 'meta.json')

        self._ensure_files()

    def _ensure_files(self):
        defaults = {
            self.working_path: [],
            self.episodic_path: [],
            self.historical_path: [],
            self.global_path: {'branch_ids': [], 'summary': '', 'created_at': ''},
            self.meta_path: {'current_segment': 1, 'total_messages': 0, 'next_episode_idx': 0, 'next_branch_episode_idx': 0}
        }
        for path, content in defaults.items():
            if not os.path.exists(path):
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(content, f, ensure_ascii=False, indent=2)
        # Ensure first raw segment
        raw1 = self._raw_filename(1)
        if not os.path.exists(raw1):
            with open(raw1, 'w', encoding='utf-8') as f:
                json.dump({'history': []}, f, ensure_ascii=False, indent=2)

    def _raw_filename(self, seg: int) -> str:
        return os.path.join(self.base_dir, f'raw_{seg}.json')

    def _load_meta(self) -> dict:
        with open(self.meta_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_meta(self, meta: dict):
        with open(self.meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

    def record_interaction(self, role: str, content: str, timestamp: datetime = None):
        ts = (timestamp or datetime.utcnow()).isoformat()
        meta = self._load_meta()
        seg = meta['current_segment']
        total = meta['total_messages']

        # Write to current raw segment
        raw_file = self._raw_filename(seg)
        with open(raw_file, 'r+', encoding='utf-8') as rf:
            data = json.load(rf)
            data['history'].append({
                'segment': seg,
                'offset': len(data['history']),
                'speaker': role,
                'text': content,
                'timestamp': ts
            })
            rf.seek(0)
            json.dump(data, rf, ensure_ascii=False, indent=2)
            rf.truncate()

        # Update meta and create new segment if needed
        total += 1
        if total % self.segment_size == 0:
            seg += 1
            with open(self._raw_filename(seg), 'w', encoding='utf-8') as nf:
                json.dump({'history': []}, nf, ensure_ascii=False, indent=2)
        meta['current_segment'] = seg
        meta['total_messages'] = total
        self._save_meta(meta)

        # Update working memory
        recents = self._get_recent_raw(meta)
        with open(self.working_path, 'w', encoding='utf-8') as wf:
            json.dump(recents, wf, ensure_ascii=False, indent=2)

        # Sumarize episodic if block complete
        if total >= self.episodic_size and total % self.episodic_size == 0:
            start = meta['next_episode_idx']
            end = total
            self._summarize_episode(start, end)

    def _get_recent_raw(self, meta: dict) -> list:
        need = self.working_size
        recents = []
        seg = meta['current_segment']
        while need > 0 and seg >= 1:
            with open(self._raw_filename(seg), 'r', encoding='utf-8') as rf:
                hist = json.load(rf)['history']
            take = min(need, len(hist))
            recents = hist[-take:] + recents
            need -= take
            seg -= 1
        return recents

    def get_recent(self, n: int = None) -> list:
        n = n or self.working_size
        return self._get_recent_raw(self._load_meta())[-n:]

    def get_all(self) -> list:
        meta = self._load_meta()
        all_msgs = []
        for s in range(1, meta['current_segment'] + 1):
            with open(self._raw_filename(s), 'r', encoding='utf-8') as rf:
                all_msgs.extend(json.load(rf)['history'])
        return all_msgs

    def _summarize_episode(self, start_idx: int, end_idx: int):
        all_msgs = self.get_all()
        block = all_msgs[start_idx:end_idx]
        texts = [f"{m['speaker']}: {m['text']}" for m in block]
        summary = gerar_resumo_com_ia(texts)
        created = datetime.utcnow().isoformat()

        with open(self.episodic_path, 'r+', encoding='utf-8') as ef:
            episodes = json.load(ef)
            ep_id = len(episodes) + 1
            episodes.append({
                'episode_id': ep_id,
                'start_idx': start_idx,
                'end_idx': end_idx,
                'summary': summary,
                'created_at': created
            })
            ef.seek(0)
            json.dump(episodes, ef, ensure_ascii=False, indent=2)
            ef.truncate()

        meta = self._load_meta()
        meta['next_episode_idx'] = end_idx
        self._save_meta(meta)

        # Consolidate branches
        self._maybe_consolidate_branches(episodes)

    def _maybe_consolidate_branches(self, episodes: list):
        meta = self._load_meta()
        next_start = meta.get('next_branch_episode_idx', 0)
        remaining = [e for e in episodes if e['episode_id'] > next_start]
        if len(remaining) >= self.branch_size:
            batch = remaining[:self.branch_size]
            texts = [ep['summary'] for ep in batch]
            branch_summary = gerar_resumo_com_ia(texts)
            created = datetime.utcnow().isoformat()

            with open(self.historical_path, 'r+', encoding='utf-8') as hf:
                branches = json.load(hf)
                br_id = len(branches) + 1
                branches.append({
                    'branch_id': br_id,
                    'episodes': [ep['episode_id'] for ep in batch],
                    'summary': branch_summary,
                    'created_at': created
                })
                hf.seek(0)
                json.dump(branches, hf, ensure_ascii=False, indent=2)
                hf.truncate()

            meta['next_branch_episode_idx'] = batch[-1]['episode_id']
            self._save_meta(meta)

            # Update global every 4 branches
            if len(branches) % 4 == 0:
                self.update_global_summary()

    def update_global_summary(self):
        with open(self.historical_path, 'r', encoding='utf-8') as hf:
            branches = json.load(hf)
        if not branches:
            return
        texts = [b['summary'] for b in branches]
        summary = gerar_resumo_com_ia(texts)
        created = datetime.utcnow().isoformat()
        with open(self.global_path, 'w', encoding='utf-8') as gf:
            json.dump({
                'branch_ids': [b['branch_id'] for b in branches],
                'summary': summary,
                'created_at': created
            }, gf, ensure_ascii=False, indent=2)

    def retrieve(self, query: str, top_k: int = 3) -> list:
        with open(self.historical_path, 'r', encoding='utf-8') as hf:
            branches = json.load(hf)[-top_k:]
        with open(self.episodic_path, 'r', encoding='utf-8') as ef:
            episodes = json.load(ef)
        all_msgs = self.get_all()
        passages = []
        for br in branches:
            for ep_id in br['episodes']:
                ep = next(e for e in episodes if e['episode_id']==ep_id)
                passages.extend(all_msgs[ep['start_idx']:ep['end_idx']])
        return passages