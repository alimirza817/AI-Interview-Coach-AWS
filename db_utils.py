import boto3
from boto3.dynamodb.conditions import Attr
import uuid
from datetime import datetime

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
table    = dynamodb.Table("interview_history1")


def save_message(session_id: str, role: str, content: str):
    """Save one chat message. role = 'user' or 'assistant'."""
    table.put_item(Item={
        "id":         str(uuid.uuid4()),
        "session_id": session_id,
        "role":       role,
        "content":    content,          # ← always 'content', fixes KeyError
        "timestamp":  datetime.utcnow().isoformat()
    })


def get_session_messages(session_id: str) -> list:
    """Return all messages for a session as [{'role':..,'content':..}]."""
    response = table.scan(FilterExpression=Attr("session_id").eq(session_id))
    items    = sorted(response.get("Items", []), key=lambda x: x.get("timestamp", ""))
    return [{"role": i["role"], "content": i["content"]} for i in items]


def get_all_sessions() -> list:
    """Return latest sessions for sidebar."""
    response = table.scan()
    items    = sorted(response.get("Items", []),
                      key=lambda x: x.get("timestamp", ""), reverse=True)
    seen, sessions = set(), []
    for item in items:
        sid = item.get("session_id", "")
        if sid not in seen:
            seen.add(sid)
            sessions.append({
                "session_id": sid,
                "timestamp":  item.get("timestamp", "")[:16],
                "preview":    item.get("content", "")[:60]
            })
    return sessions


def save_score(session_id: str, score_report: str):
    """Persist the final score report."""
    table.put_item(Item={
        "id":         str(uuid.uuid4()),
        "session_id": session_id,
        "role":       "score_report",
        "content":    score_report,
        "timestamp":  datetime.utcnow().isoformat()
    })