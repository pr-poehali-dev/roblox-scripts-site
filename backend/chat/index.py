import json
import os
import psycopg2

def get_db():
    return psycopg2.connect(os.environ["DATABASE_URL"])

def handler(event, context):
    """Чат поддержки между пользователями и админом"""
    if event.get("httpMethod") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, X-User-Id, X-Auth-Token",
                "Access-Control-Max-Age": "86400",
            },
            "body": "",
        }

    headers = {"Access-Control-Allow-Origin": "*", "Content-Type": "application/json"}
    h = event.get("headers", {}) or {}
    user_id = h.get("X-User-Id") or h.get("x-user-id")

    if not user_id:
        return {"statusCode": 401, "headers": headers, "body": json.dumps({"error": "Не авторизован"})}

    user_id = int(user_id)
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT role, is_blocked FROM users WHERE id = %d" % user_id)
    user_row = cur.fetchone()
    if not user_row:
        cur.close()
        conn.close()
        return {"statusCode": 401, "headers": headers, "body": json.dumps({"error": "Пользователь не найден"})}

    is_admin = user_row[0] == "admin"

    if user_row[1] and not is_admin:
        cur.close()
        conn.close()
        return {"statusCode": 403, "headers": headers, "body": json.dumps({"error": "Аккаунт заблокирован"})}

    method = event.get("httpMethod", "GET")
    params = event.get("queryStringParameters", {}) or {}
    action = params.get("action", "messages")

    if method == "GET" and action == "messages":
        if is_admin:
            target_user = params.get("user_id")
            if target_user:
                cur.execute(
                    "SELECT m.id, m.user_id, m.message, m.is_from_admin, m.is_read, m.created_at, u.username "
                    "FROM chat_messages m JOIN users u ON m.user_id = u.id "
                    "WHERE m.user_id = %d ORDER BY m.created_at ASC" % int(target_user)
                )
            else:
                cur.execute(
                    "SELECT DISTINCT ON (m.user_id) m.user_id, u.username, m.message, m.created_at, "
                    "(SELECT COUNT(*) FROM chat_messages cm WHERE cm.user_id = m.user_id AND cm.is_read = FALSE AND cm.is_from_admin = FALSE) as unread "
                    "FROM chat_messages m JOIN users u ON m.user_id = u.id "
                    "ORDER BY m.user_id, m.created_at DESC"
                )
                chats = []
                for r in cur.fetchall():
                    chats.append({
                        "user_id": r[0],
                        "username": r[1],
                        "last_message": r[2],
                        "last_at": r[3].isoformat() if r[3] else None,
                        "unread": r[4],
                    })
                cur.close()
                conn.close()
                return {"statusCode": 200, "headers": headers, "body": json.dumps({"chats": chats})}
        else:
            cur.execute(
                "SELECT m.id, m.user_id, m.message, m.is_from_admin, m.is_read, m.created_at "
                "FROM chat_messages m WHERE m.user_id = %d ORDER BY m.created_at ASC" % user_id
            )

        messages = []
        for r in cur.fetchall():
            messages.append({
                "id": r[0],
                "user_id": r[1],
                "message": r[2],
                "is_from_admin": r[3],
                "is_read": r[4],
                "created_at": r[5].isoformat() if r[5] else None,
            })

        cur.close()
        conn.close()
        return {"statusCode": 200, "headers": headers, "body": json.dumps({"messages": messages})}

    if method == "POST" and action == "send":
        body = json.loads(event.get("body", "{}"))
        message = body.get("message", "").strip()

        if not message:
            cur.close()
            conn.close()
            return {"statusCode": 400, "headers": headers, "body": json.dumps({"error": "Сообщение не может быть пустым"})}

        if len(message) > 2000:
            cur.close()
            conn.close()
            return {"statusCode": 400, "headers": headers, "body": json.dumps({"error": "Сообщение слишком длинное"})}

        if is_admin:
            target_user = body.get("user_id")
            if not target_user:
                cur.close()
                conn.close()
                return {"statusCode": 400, "headers": headers, "body": json.dumps({"error": "user_id обязателен для админа"})}
            cur.execute(
                "INSERT INTO chat_messages (user_id, message, is_from_admin) VALUES (%d, '%s', TRUE) RETURNING id, created_at"
                % (int(target_user), message.replace("'", "''"))
            )
        else:
            cur.execute(
                "INSERT INTO chat_messages (user_id, message, is_from_admin) VALUES (%d, '%s', FALSE) RETURNING id, created_at"
                % (user_id, message.replace("'", "''"))
            )

        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return {"statusCode": 200, "headers": headers, "body": json.dumps({"id": row[0], "created_at": row[1].isoformat()})}

    if method == "POST" and action == "read":
        body = json.loads(event.get("body", "{}"))
        if is_admin:
            target_user = body.get("user_id")
            if target_user:
                cur.execute("UPDATE chat_messages SET is_read = TRUE WHERE user_id = %d AND is_from_admin = FALSE" % int(target_user))
        else:
            cur.execute("UPDATE chat_messages SET is_read = TRUE WHERE user_id = %d AND is_from_admin = TRUE" % user_id)

        conn.commit()
        cur.close()
        conn.close()
        return {"statusCode": 200, "headers": headers, "body": json.dumps({"success": True})}

    cur.close()
    conn.close()
    return {"statusCode": 400, "headers": headers, "body": json.dumps({"error": "Неизвестное действие"})}
