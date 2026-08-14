"""Knowledge base.

A minimal, dependency-free retrieval interface. The default implementation is
an in-memory keyword index; a production deployment swaps in a vector store by
implementing the same interface.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Document:
    id: str
    text: str
    source: str = ""

    def to_dict(self) -> dict:
        return {"id": self.id, "text": self.text, "source": self.source}


@dataclass
class KnowledgeBase:
    """In-memory keyword-search knowledge base (swap for a vector store later)."""

    docs: Dict[str, Document] = field(default_factory=dict)
    _index: Dict[str, List[str]] = field(default_factory=dict, init=False)

    def add(self, text: str, source: str = "") -> str:
        doc_id = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
        self.docs[doc_id] = Document(doc_id, text, source)
        for token in re.findall(r"[a-z0-9]+", text.lower()):
            self._index.setdefault(token, []).append(doc_id)
        return doc_id

    def search(self, query: str, top_k: int = 3) -> List[Document]:
        tokens = re.findall(r"[a-z0-9]+", query.lower())
        if not tokens:
            return []
        scores: Dict[str, int] = {}
        for token in tokens:
            for doc_id in self._index.get(token, []):
                scores[doc_id] = scores.get(doc_id, 0) + 1
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        return [self.docs[did] for did, _ in ranked[:top_k]]
