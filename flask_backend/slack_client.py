import os
from typing import Any, Dict, List, Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

class SlackClient:
    """
    Lightweight wrapper around slack_sdk.WebClient to encapsulate a few operations:
    - validate_channel(channel_id)
    - fetch_recent_messages(channel_id)
    - resolve_user(user_id)
    - build_thread_url(channel_id, ts)
    """

    def __init__(self, bot_token: str):
        if not bot_token:
            raise ValueError("SLACK_BOT_TOKEN is required")
        self.client = WebClient(token=bot_token)

    # PUBLIC_INTERFACE
    def validate_channel(self, channel_id: str) -> bool:
        """Validate that a channel exists and is accessible."""
        try:
            resp = self.client.conversations_info(channel=channel_id)
            return bool(resp and resp.get("ok"))
        except SlackApiError:
            return False

    # PUBLIC_INTERFACE
    def fetch_recent_messages(self, channel_id: str, limit: int = 200) -> List[Dict[str, Any]]:
        """
        Fetch recent messages from a channel.
        Includes top-level messages; threads can be referenced via thread_ts.
        """
        try:
            resp = self.client.conversations_history(channel=channel_id, limit=limit)
            if not resp or not resp.get("ok"):
                return []
            messages = resp.get("messages") or []
            # Optional: enrich with reply_count via conversations_replies for each with thread_ts (skipped for speed)
            return messages
        except SlackApiError as e:
            raise RuntimeError(f"Slack API error: {e.response['error'] if hasattr(e, 'response') else str(e)}")

    # PUBLIC_INTERFACE
    def resolve_user(self, user_id: Optional[str]) -> str:
        """Resolve a Slack user ID to displayable name."""
        if not user_id:
            return ""
        try:
            resp = self.client.users_info(user=user_id)
            if resp and resp.get("ok"):
                user = (resp.get("user") or {})
                profile = user.get("profile") or {}
                return profile.get("display_name") or profile.get("real_name") or user.get("name") or user_id
        except SlackApiError:
            pass
        return str(user_id)

    # PUBLIC_INTERFACE
    def build_thread_url(self, channel_id: str, ts: Optional[str]) -> str:
        """
        Build a Slack thread URL given a channel ID and a ts value.

        Slack URL format:
          https://app.slack.com/client/<team>/C123?threadTs=123.456&cid=C123
        or the classic permalink:
          https://slack.com/archives/<channel_id>/p<ts_without_dot>

        We will return the classic permalink using chat_getPermalink when possible.
        """
        if not ts:
            return ""
        try:
            resp = self.client.chat_getPermalink(channel=channel_id, message_ts=ts)
            if resp and resp.get("ok"):
                return resp.get("permalink") or ""
        except SlackApiError:
            pass
        # Fallback classic guess (may not work without team context)
        ts_compact = str(ts).replace(".", "")
        return f"https://slack.com/archives/{channel_id}/p{ts_compact}"
