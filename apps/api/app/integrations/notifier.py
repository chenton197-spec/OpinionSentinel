from __future__ import annotations


def send_notification(channel: str, payload: dict) -> dict:
    return {
        "channel": channel,
        "status": "mocked",
        "message": f"Notification prepared for {channel}",
        "payload": payload,
    }
