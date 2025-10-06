import os
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from flask import Flask, jsonify, request, send_file, make_response
from flask_cors import CORS
from werkzeug.exceptions import BadRequest, NotFound

from models import QueryItem, ChannelConfig
from storage import get_storage_backend
from slack_client import SlackClient
from exporter import Exporter

# PUBLIC_INTERFACE
def create_app() -> Flask:
    """
    Create and configure the Flask application.

    Environment variables:
    - FLASK_ENV: Flask environment (default: development)
    - PORT: Port to run the server on (default: 5000)
    - FRONTEND_ORIGIN: Allowed origin for CORS (default: http://localhost:3000)
    - SLACK_BOT_TOKEN: Slack bot token for API calls
    - STORAGE_BACKEND: Storage backend (default: json)
    - STORAGE_FILE: Path to JSON file storage (default: data/queries.json)

    Returns:
        Configured Flask app instance.
    """
    app = Flask(__name__)

    # Config and CORS
    frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
    CORS(
        app,
        resources={r"/api/*": {"origins": [frontend_origin]}},
        supports_credentials=False,
        methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    # Storage and integrations (lazy-init inside handlers when needed)
    storage = get_storage_backend(
        backend=os.getenv("STORAGE_BACKEND", "json"),
        file_path=os.getenv("STORAGE_FILE", os.path.join(os.path.dirname(__file__), "data", "queries.json")),
    )
    slack_token = os.getenv("SLACK_BOT_TOKEN", "").strip()
    slack = SlackClient(slack_token) if slack_token else None
    exporter = Exporter()

    # Helpers
    def _json_error(message: str, code: int = 400):
        resp = jsonify({"error": message, "code": code})
        return make_response(resp, code)

    def _parse_pagination() -> Tuple[int, int]:
        try:
            page = int(request.args.get("page", "1"))
            page_size = int(request.args.get("pageSize", "10"))
            page = max(1, page)
            page_size = min(max(1, page_size), 100)
            return page, page_size
        except ValueError:
            raise BadRequest("Invalid pagination parameters")

    # Routes

    @app.route("/api/config/channel", methods=["GET"])
    def get_config_channel():
        """
        Get saved Slack channel configuration.

        Returns:
            JSON with { channel_id, channel_name, valid }.
        """
        cfg = storage.get_channel_config()
        if not cfg:
            return jsonify({"channel_id": "", "channel_name": "", "valid": False})
        valid = False
        if slack:
            try:
                valid = slack.validate_channel(cfg.channel_id)
            except Exception:
                valid = False
        return jsonify({"channel_id": cfg.channel_id, "channel_name": cfg.channel_name or "", "valid": valid})

    @app.route("/api/config/channel", methods=["POST"])
    def post_config_channel():
        """
        Save Slack channel configuration.

        Body:
            { "channel_id": "C0123...", "channelId": "...", "channel_name": "...", "channelName": "..." }

        Returns:
            JSON with { channel_id, channel_name, valid }.
        """
        data = request.get_json(silent=True) or {}
        channel_id = data.get("channel_id") or data.get("channelId")
        channel_name = data.get("channel_name") or data.get("channelName") or ""
        if not channel_id or not isinstance(channel_id, str):
            return _json_error("channel_id is required", 400)
        # Validate with Slack if possible
        valid = False
        if slack:
            try:
                valid = slack.validate_channel(channel_id)
            except Exception as e:
                return _json_error(f"Slack validation failed: {e}", 400)
        cfg = ChannelConfig(channel_id=channel_id.strip(), channel_name=(channel_name or "").strip())
        storage.save_channel_config(cfg)
        return jsonify({"channel_id": cfg.channel_id, "channel_name": cfg.channel_name, "valid": valid})

    @app.route("/api/queries", methods=["GET"])
    def get_queries():
        """
        List queries with optional filters.

        Query params:
            - status: filter by status
            - search: search in user, resolver, thread_url
            - page: page number (1+)
            - pageSize: page size (1-100)

        Returns:
            { "items": [QueryItem...], "total": <int> }
        """
        status = request.args.get("status", "").strip()
        search = request.args.get("search", "").strip().lower()
        page, page_size = _parse_pagination()
        items = storage.list_queries()
        # Filter
        if status:
            items = [i for i in items if (i.status or "").lower() == status.lower()]
        if search:
            def _hit(it: QueryItem) -> bool:
                return any(
                    (field or "").lower().find(search) >= 0
                    for field in [it.user, it.resolver, it.thread_url]
                )
            items = [i for i in items if _hit(i)]
        total = len(items)
        start = (page - 1) * page_size
        end = start + page_size
        page_items = items[start:end]
        return jsonify({"items": [i.to_dict() for i in page_items], "total": total})

    @app.route("/api/queries", methods=["POST"])
    def post_queries():
        """
        Create a new manual query entry.

        Body:
            {
                "user": "<str, required>",
                "thread_url": "<str, required>",
                "resolver": "<str, optional>",
                "status": "open|in_progress|resolved"
            }

        Returns:
            Created QueryItem as JSON.
        """
        data = request.get_json(silent=True) or {}
        user = (data.get("user") or "").strip()
        thread_url = (data.get("thread_url") or "").strip()
        if not user or not thread_url:
            return _json_error("user and thread_url are required", 400)
        status = (data.get("status") or "open").strip() or "open"
        resolver = (data.get("resolver") or "").strip()
        now = datetime.utcnow().isoformat()
        item = QueryItem(
            id=None,
            user=user,
            thread_url=thread_url,
            resolver=resolver or "",
            status=status,
            created_at=now,
            resolved_at=(now if status == "resolved" else None),
        )
        saved = storage.create_query(item)
        return jsonify(saved.to_dict()), 201

    @app.route("/api/queries/<id>", methods=["PATCH"])
    def patch_query(id: str):
        """
        Partially update a query.

        Body:
            Supports fields: resolver, status, resolved_at

        Behavior:
            - If status is set to 'resolved' and resolved_at is missing -> set resolved_at = now.
            - If status is changed from 'resolved' to anything else -> resolved_at = None

        Returns:
            Updated QueryItem as JSON.
        """
        if not id:
            return _json_error("id is required", 400)
        item = storage.get_query(id)
        if not item:
            raise NotFound("Query not found")
        data = request.get_json(silent=True) or {}
        status = data.get("status")
        resolver = data.get("resolver")
        resolved_at = data.get("resolved_at")
        if resolver is not None:
            item.resolver = (resolver or "").strip()
        if status is not None:
            status = (status or "").strip() or item.status
            if status == "resolved":
                # If no resolved_at coming, set current time
                if not resolved_at:
                    item.resolved_at = datetime.utcnow().isoformat()
                else:
                    item.resolved_at = resolved_at
            else:
                # If moving away from resolved, clear resolved_at unless client sets explicitly
                if resolved_at is None:
                    item.resolved_at = None
                else:
                    item.resolved_at = resolved_at
            item.status = status
        elif resolved_at is not None:
            item.resolved_at = resolved_at
        updated = storage.update_query(item)
        return jsonify(updated.to_dict())

    @app.route("/api/queries/<id>", methods=["DELETE"])
    def delete_query(id: str):
        """
        Delete a query by ID.

        Returns:
            { "ok": true }
        """
        if not id:
            return _json_error("id is required", 400)
        ok = storage.delete_query(id)
        if not ok:
            raise NotFound("Query not found")
        return jsonify({"ok": True})

    @app.route("/api/slack/fetch", methods=["POST"])
    def slack_fetch():
        """
        Fetch recent messages from the configured Slack channel and upsert entries.

        Heuristic for a "query":
            - Message has a thread (reply_count > 0 or thread_ts exists)
            - And text contains '?' or 'help' (case-insensitive)

        Upsert key:
            - based on thread URL (constructed from channel + ts)

        Returns:
            { "fetched": <int>, "upserts": <int> }
        """
        if not slack:
            return _json_error("Slack is not configured (missing SLACK_BOT_TOKEN)", 400)
        cfg = storage.get_channel_config()
        if not cfg or not cfg.channel_id:
            return _json_error("Channel is not configured", 400)
        try:
            messages = slack.fetch_recent_messages(cfg.channel_id)
        except Exception as e:
            return _json_error(f"Slack fetch failed: {e}", 400)

        def looks_like_query(msg: Dict[str, Any]) -> bool:
            text = (msg.get("text") or "").lower()
            has_thread = bool(msg.get("thread_ts") or (msg.get("reply_count") or 0) > 0)
            return has_thread and ("?" in text or "help" in text)

        upserts = 0
        fetched = len(messages or [])
        for m in messages or []:
            if not looks_like_query(m):
                continue
            user_name = slack.resolve_user(m.get("user")) or "unknown"
            ts = m.get("thread_ts") or m.get("ts")
            thread_url = slack.build_thread_url(cfg.channel_id, ts) if ts else ""
            if not thread_url:
                continue
            # If existing, keep existing resolver/status unless already resolved
            existing = storage.get_by_thread_url(thread_url)
            if existing:
                # we could update fields from Slack if needed; for now ensure user is set
                if not existing.user and user_name:
                    existing.user = user_name
                storage.update_query(existing)
                upserts += 1
                continue
            # Create new
            item = QueryItem(
                id=None,
                user=user_name,
                thread_url=thread_url,
                resolver="",
                status="open",
                created_at=datetime.utcnow().isoformat(),
                resolved_at=None,
            )
            storage.create_query(item)
            upserts += 1

        return jsonify({"fetched": fetched, "upserts": upserts})

    @app.route("/api/export", methods=["POST"])
    def export_excel():
        """
        Generate an Excel export of the current queries and return as binary.

        Returns:
            application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
        """
        items = storage.list_queries()
        file_path = exporter.export(items)
        # send_file needs an absolute path
        response = send_file(
            file_path,
            as_attachment=True,
            download_name=f"slack-queries-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            max_age=0,
        )
        return response

    @app.route("/api/health", methods=["GET"])
    def health():
        """Simple health endpoint."""
        return jsonify({"ok": True})

    return app


if __name__ == "__main__":
    # Allow running as script
    app = create_app()
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_ENV", "development") == "development")
