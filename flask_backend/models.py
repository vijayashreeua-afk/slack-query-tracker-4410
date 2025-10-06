from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import uuid

# PUBLIC_INTERFACE
@dataclass
class ChannelConfig:
    """Slack channel configuration model."""
    channel_id: str
    channel_name: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"channel_id": self.channel_id, "channel_name": self.channel_name}


# PUBLIC_INTERFACE
@dataclass
class QueryItem:
    """Represents a tracked Slack query item."""
    id: Optional[str]
    user: str
    thread_url: str
    resolver: str = ""
    status: str = "open"  # open | in_progress | resolved
    created_at: Optional[str] = None
    resolved_at: Optional[str] = None

    def ensure_id(self):
        if not self.id:
            self.id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user": self.user,
            "thread_url": self.thread_url,
            "resolver": self.resolver,
            "status": self.status,
            "created_at": self.created_at,
            "resolved_at": self.resolved_at,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "QueryItem":
        return QueryItem(
            id=d.get("id"),
            user=d.get("user", ""),
            thread_url=d.get("thread_url", ""),
            resolver=d.get("resolver", ""),
            status=d.get("status", "open"),
            created_at=d.get("created_at"),
            resolved_at=d.get("resolved_at"),
        )
