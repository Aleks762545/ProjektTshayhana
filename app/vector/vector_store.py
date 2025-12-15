import os, json, numpy as np
from app.config import settings
PERSIST = settings['vector']['persist_dir']
os.makedirs(PERSIST, exist_ok=True)
EMB_FILE = os.path.join(PERSIST, 'embeddings.npy')
META_FILE = os.path.join(PERSIST, 'meta.json')

class NumpyVectorStore:
    def __init__(self):
        self._emb = None
        self._ids = []
        self._meta = {}
        self._load()

    def _load(self):
        if os.path.exists(EMB_FILE):
            self._emb = np.load(EMB_FILE)
        else:
            self._emb = np.zeros((0,1))
        if os.path.exists(META_FILE):
            with open(META_FILE,'r',encoding='utf-8') as f:
                self._meta = json.load(f)
                self._ids = list(self._meta.keys())
        else:
            self._meta = {}
            self._ids = []

    def _save(self):
        np.save(EMB_FILE, self._emb)
        with open(META_FILE,'w',encoding='utf-8') as f:
            json.dump(self._meta, f, ensure_ascii=False, indent=2)

    def upsert(self, id, emb, metadata):
        id = str(id)
        emb = np.array(emb, dtype='float32')
        if self._emb.size == 0:
            self._emb = emb.reshape(1,-1)
            self._ids = [id]
        else:
            # ensure dims
            if emb.shape[0] != self._emb.shape[1]:
                # resize existing to match new dim by padding zeros (rare)
                if emb.shape[0] > self._emb.shape[1]:
                    pad = np.zeros((self._emb.shape[0], emb.shape[0]-self._emb.shape[1]), dtype='float32')
                    self._emb = np.hstack([self._emb, pad])
                else:
                    emb = np.pad(emb, (0, self._emb.shape[1]-emb.shape[0]), 'constant').astype('float32')
            if id in self._ids:
                idx = self._ids.index(id)
                self._emb[idx] = emb
            else:
                self._emb = np.vstack([self._emb, emb])
                self._ids.append(id)
        self._meta[id] = metadata
        self._save()

    def delete(self, id):
        id = str(id)
        if id in self._ids:
            idx = self._ids.index(id)
            self._emb = np.delete(self._emb, idx, axis=0)
            self._ids.pop(idx)
            self._meta.pop(id, None)
            self._save()

    def query(self, emb, top_k=10):
        if self._emb.size == 0:
            return []
        emb = np.array(emb, dtype='float32')
        # normalize
        def norm(a):
            n = np.linalg.norm(a, axis=1, keepdims=True)
            n[n==0]=1
            return a / n
        A = norm(self._emb)
        v = emb.reshape(1,-1)
        v = v / (np.linalg.norm(v)+1e-10)
        sims = (A @ v.T).reshape(-1)
        idxs = sims.argsort()[::-1][:top_k]
        res = []
        for i in idxs:
            res.append({'id': int(self._ids[i]), 'score': float(sims[i]), 'metadata': self._meta.get(self._ids[i], {})})
        return res

VECTOR_STORE = NumpyVectorStore()
