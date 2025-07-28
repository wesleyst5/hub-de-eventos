import jwt
from flask import request
import os

JWT_SECRET = os.getenv("JWT_SECRET", "supersecretkey")

def authenticate_request(request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except Exception:
        return None
