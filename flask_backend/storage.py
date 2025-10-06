import json
import os
from threading import RLock
from typing import List, Optional, Dict, Any

from models import QueryItem, ChannelConfig

class BaseStorage:
    """Abstract storage interface used by the app. For step 3 this can be extended/replaced."""

    # PUBLIC_INTERFACE
    def get_channel_config(self) -> Optional[ChannelConfig]:
        """Return current channel configuration if set."""
        raise NotImplementedError

    # PUBLIC_INTERFACE
    def save_channel_config(self, cfg: ChannelConfig) -> None:
        """Persist channel configuration."""
        raise NotImplementedError

    # PUBLIC_INTERFACE
    def list_queries(self) -> List[QueryItem]:
        """Return all queries."""
        raise NotImplementedError

    # PUBLIC_INTERFACE
    def create_query(self, item: QueryItem) -> QueryItem:
        """Create and persist a new query item."""
        raise NotImplementedError

    # PUBLIC_INTERFACE
    def get_query(self, id: str) -> Optional[QueryItem]:
        """Get query by ID."""
        raise NotImplementedError

    # PUBLIC_INTERFACE
    def update_query(self, item: QueryItem) -> QueryItem:
        """Update a query item."""
        raise NotImplementedError

    # PUBLIC_INTERFACE
    def delete_query(self, id: str) -> bool:
        """Delete a query by ID. Returns True if deleted."""
        raise NotImplementedError

    # PUBLIC_INTERFACE
    def get_by_thread_url(self, thread_url: str) -> Optional[QueryItem]:
        """Find a query by thread URL."""
        raise NotImplementedError


class JsonStorage(BaseStorage):
    """Simple JSON-file based storage backend."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.lock = RLock()
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        # Initialize file if missing
        if not os.path.exists(self.file_path):
            self._write({"channel": {"channel_id": "", "channel_name": ""}, "queries": []})

    def _read(self) -> Dict[str, Any]:
        with self.lock:
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {"channel": {"channel_id": "", "channel_name": ""}, "queries": []}

    def _write(self, data: Dict[str, Any]) -> None:
        with self.lock:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

    def get_channel_config(self) -> Optional[ChannelConfig]:
        data = self._read()
        ch = data.get("channel") or {}
        channel_id = (ch.get("channel_id") or "").strip()
        channel_name = (ch.get("channel_name") or "").strip()
        if not channel_id:
            return None
        return ChannelConfig(channel_id=channel_id, channel_name=channel_name)

    def save_channel_config(self, cfg: ChannelConfig) -> None:
        data = self._read()
        data["channel"] = cfg.to_dict()
        self._write(data)

    def list_queries(self) -> List[QueryItem]:
        data = self._read()
        return [QueryItem.from_dict(x) for x in (data.get("queries") or [])]

    def _save_queries(self, items: List[QueryItem]) -> None:
        data = self._read()
        data["queries"] = [i.to_dict() for i in items]
        self._write(data)

    def create_query(self, item: QueryItem) -> QueryItem:
        item.ensure_id()
        items = self.list_queries()
        items.append(item)
        self._save_queries(items)
        return item

    def get_query(self, id: str) -> Optional[QueryItem]:
        for it in self.list_queries():
            if it.id == id:
                return it
        return None

    def update_query(self, item: QueryItem) -> QueryItem:
        items = self.list_queries()
        for idx, it in enumerate(items):
            if it.id == item.id:
                items[idx] = item
                self._save_queries(items)
                return item
        # If not found, create it
        items.append(item)
        self._save_queries(items)
        return item

    def delete_query(self, id: str) -> bool:
        items = self.list_queries()
        new_items = [it for it in items if it.id != id]
        deleted = len(new_items) != len(items)
        if deleted:
            self._save_queries(new_items)
        return deleted

    def get_by_thread_url(self, thread_url: str) -> Optional[QueryItem]:
        for it in self.list_queries():
            if (it.thread_url or "").strip() == (thread_url or "").strip():
                return it
        return None


# PUBLIC_INTERFACE
def get_storage_backend(backend: str = "json", file_path: Optional[str] = None) -> BaseStorage:
    """
    Create a storage backend instance.

    Args:
        backend: backend name (currently supports 'json')
        file_path: path to storage file (for json backend)

    Returns:
        BaseStorage implementation.
    """
    if backend == "json":
        path = file_path or os.path.join(os.path.dirname(__file__), "data", "queries.json")
        return JsonStorage(path)
    raise ValueError(f"Unsupported storage backend: {backend}")
