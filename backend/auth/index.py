import json
import os
import hashlib
import secrets
import psycopg2

def get_db():
    return psycopg2.connect(os.environ["DATABASE_URL"])

def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{hashed}"

def verify_password(password, stored):
    salt, hashed = stored.split(":")
    return hash_password(password, salt) == stored

def handler(event, context):
    """Авторизация и регистрация пользователей"""
    if event.get("httpMethod") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Auth-Token, X-User-Id",
                "Access-Control-Max-Age": "86400",
            },
            "body": "",
        }

    headers = {"Access-Control-Allow-Origin": "*", "Content-Type": "application/json"}
    method = event.get("httpMethod", "GET")
    path = event.get("queryStringParameters", {}) or {}
    action = path.get("action", "")

    if method == "POST":
        body = json.loads(event.get("body", "{}"))
        username = body.get("username", "").strip().lower()
        password = body.get("password", "")

        if not username or not password:
            return {"statusCode": 400, "headers": headers, "body": json.dumps({"error": "Логин и пароль обязательны"})}

        if len(username) < 3 or len(username) > 50:
            return {"statusCode": 400, "headers": headers, "body": json.dumps({"error": "Логин от 3 до 50 символов"})}

        if len(password) < 6:
            return {"statusCode": 400, "headers": headers, "body": json.dumps({"error": "Пароль минимум 6 символов"})}

        conn = get_db()
        cur = conn.cursor()

        if action == "register":
            cur.execute("SELECT id FROM users WHERE username = '%s'" % username.replace("'", "''"))
            if cur.fetchone():
                cur.close()
                conn.close()
                return {"statusCode": 400, "headers": headers, "body": json.dumps({"error": "Такой логин уже занят"})}

            password_hash = hash_password(password)
            cur.execute(
                "INSERT INTO users (username, password_hash) VALUES ('%s', '%s') RETURNING id, username, role, is_blocked"
                % (username.replace("'", "''"), password_hash.replace("'", "''"))
            )
            user = cur.fetchone()
            conn.commit()

            token = secrets.token_hex(32)
            cur.close()
            conn.close()
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps({
                    "user": {"id": user[0], "username": user[1], "role": user[2], "is_blocked": user[3]},
                    "token": token,
                }),
            }

        elif action == "login":
            cur.execute(
                "SELECT id, username, password_hash, role, is_blocked, blocked_reason FROM users WHERE username = '%s'"
                % username.replace("'", "''")
            )
            user = cur.fetchone()
            if not user:
                cur.close()
                conn.close()
                return {"statusCode": 401, "headers": headers, "body": json.dumps({"error": "Неверный логин или пароль"})}

            if user[1] == "admin" and user[2] == "CHANGE_ME_ON_FIRST_LOGIN":
                new_hash = hash_password(password)
                cur.execute("UPDATE users SET password_hash = '%s', last_login = NOW() WHERE id = %d" % (new_hash.replace("'", "''"), user[0]))
                conn.commit()
                token = secrets.token_hex(32)
                cur.close()
                conn.close()
                return {
                    "statusCode": 200,
                    "headers": headers,
                    "body": json.dumps({
                        "user": {"id": user[0], "username": user[1], "role": user[3], "is_blocked": user[4]},
                        "token": token,
                    }),
                }

            if not verify_password(password, user[2]):
                cur.close()
                conn.close()
                return {"statusCode": 401, "headers": headers, "body": json.dumps({"error": "Неверный логин или пароль"})}

            if user[4]:
                cur.close()
                conn.close()
                return {"statusCode": 403, "headers": headers, "body": json.dumps({"error": "Аккаунт заблокирован", "reason": user[5]})}

            cur.execute("UPDATE users SET last_login = NOW() WHERE id = %d" % user[0])
            conn.commit()

            token = secrets.token_hex(32)
            cur.close()
            conn.close()
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps({
                    "user": {"id": user[0], "username": user[1], "role": user[3], "is_blocked": user[4]},
                    "token": token,
                }),
            }

    return {"statusCode": 400, "headers": headers, "body": json.dumps({"error": "Неизвестное действие"})}
