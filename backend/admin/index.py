import json
import os
import psycopg2

def get_db():
    return psycopg2.connect(os.environ["DATABASE_URL"])

def handler(event, context):
    """Админ-панель: управление пользователями и блокировки"""
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
    admin_id = h.get("X-User-Id") or h.get("x-user-id")

    if not admin_id:
        return {"statusCode": 401, "headers": headers, "body": json.dumps({"error": "Не авторизован"})}

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT role FROM users WHERE id = %s" % int(admin_id))
    row = cur.fetchone()
    if not row or row[0] != "admin":
        cur.close()
        conn.close()
        return {"statusCode": 403, "headers": headers, "body": json.dumps({"error": "Нет доступа"})}

    method = event.get("httpMethod", "GET")
    params = event.get("queryStringParameters", {}) or {}
    action = params.get("action", "list")

    if method == "GET" and action == "list":
        cur.execute("SELECT id, username, role, is_blocked, blocked_reason, created_at, last_login FROM users ORDER BY created_at DESC")
        rows = cur.fetchall()
        users = []
        for r in rows:
            users.append({
                "id": r[0],
                "username": r[1],
                "role": r[2],
                "is_blocked": r[3],
                "blocked_reason": r[4],
                "created_at": r[5].isoformat() if r[5] else None,
                "last_login": r[6].isoformat() if r[6] else None,
            })
        cur.close()
        conn.close()
        return {"statusCode": 200, "headers": headers, "body": json.dumps({"users": users})}

    if method == "GET" and action == "stats":
        cur.execute("SELECT COUNT(*) FROM users")
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM users WHERE is_blocked = TRUE")
        blocked = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM chat_messages WHERE is_read = FALSE AND is_from_admin = FALSE")
        unread = cur.fetchone()[0]
        cur.close()
        conn.close()
        return {"statusCode": 200, "headers": headers, "body": json.dumps({"total_users": total, "blocked_users": blocked, "unread_messages": unread})}

    if method == "POST" and action == "block":
        body = json.loads(event.get("body", "{}"))
        user_id = body.get("user_id")
        reason = body.get("reason", "Нарушение правил")

        if not user_id:
            cur.close()
            conn.close()
            return {"statusCode": 400, "headers": headers, "body": json.dumps({"error": "user_id обязателен"})}

        cur.execute("SELECT role FROM users WHERE id = %d" % int(user_id))
        target = cur.fetchone()
        if not target:
            cur.close()
            conn.close()
            return {"statusCode": 404, "headers": headers, "body": json.dumps({"error": "Пользователь не найден"})}
        if target[0] == "admin":
            cur.close()
            conn.close()
            return {"statusCode": 400, "headers": headers, "body": json.dumps({"error": "Нельзя заблокировать админа"})}

        cur.execute(
            "UPDATE users SET is_blocked = TRUE, blocked_reason = '%s' WHERE id = %d"
            % (reason.replace("'", "''"), int(user_id))
        )
        conn.commit()
        cur.close()
        conn.close()
        return {"statusCode": 200, "headers": headers, "body": json.dumps({"success": True})}

    if method == "POST" and action == "unblock":
        body = json.loads(event.get("body", "{}"))
        user_id = body.get("user_id")

        if not user_id:
            cur.close()
            conn.close()
            return {"statusCode": 400, "headers": headers, "body": json.dumps({"error": "user_id обязателен"})}

        cur.execute("UPDATE users SET is_blocked = FALSE, blocked_reason = NULL WHERE id = %d" % int(user_id))
        conn.commit()
        cur.close()
        conn.close()
        return {"statusCode": 200, "headers": headers, "body": json.dumps({"success": True})}

    cur.close()
    conn.close()
    return {"statusCode": 400, "headers": headers, "body": json.dumps({"error": "Неизвестное действие"})}
