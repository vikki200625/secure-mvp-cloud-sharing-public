import os
import uuid
import json
import hmac
import hashlib
import time
from datetime import datetime, timezone
import io
from flask import Flask, request, send_file, jsonify
from cryptography.fernet import Fernet


APP = Flask(__name__)

# Basic config (adjust via environment in real world)
DATA_DIR = os.path.join(os.getcwd(), "data")
KEY_FILE = os.path.join(DATA_DIR, "encryption.key")
ITEMS_FILE = os.path.join(DATA_DIR, "items.json")
LOG_FILE = os.path.join(DATA_DIR, "audit.log")
TOKEN_SECRETS = os.environ.get(
    "TOKEN_SIGNING_SECRET", "default-signing-secret-please-change"
)
API_KEY_HEADER = "X-API-KEY"
EXPECTED_API_KEY = os.environ.get("API_KEY", "college-project-key")


def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)


def load_or_init_items():
    if not os.path.exists(ITEMS_FILE):
        with open(ITEMS_FILE, "w") as f:
            json.dump({"items": []}, f)
        return {"items": []}
    with open(ITEMS_FILE, "r") as f:
        return json.load(f)


def save_items(data):
    with open(ITEMS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_encryption_key():
    if not os.path.exists(KEY_FILE):
        # generate a new key
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        return key
    with open(KEY_FILE, "rb") as f:
        return f.read()


ensure_dirs()
KEY = load_encryption_key()
FERNET = Fernet(KEY)
items_data = load_or_init_items()


def log_audit(user, item_id, action, success, source_ip=None):
    ts = datetime.now(timezone.utc).isoformat()
    line = f"{ts},{user},{item_id},{action},{success},{source_ip or ''}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)


def verify_api_key():
    key = request.headers.get(API_KEY_HEADER)
    return key == EXPECTED_API_KEY


def sign_token(payload: dict) -> str:
    payload_str = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    signature = hmac.new(
        TOKEN_SECRETS.encode(), payload_str.encode(), hashlib.sha256
    ).hexdigest()
    token = json.dumps({"payload": payload, "sig": signature}, separators=(",", ":"))
    return token


def verify_token(token_str: str):
    try:
        data = json.loads(token_str)
        payload = data.get("payload")
        sig = data.get("sig")
        if not payload or not sig:
            return None
        payload_str = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        expected_sig = hmac.new(
            TOKEN_SECRETS.encode(), payload_str.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None
        return payload
    except Exception:
        return None


@APP.route("/upload", methods=["POST"])
def upload_item():
    if not verify_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    f = request.files["file"]
    name = request.form.get("name", f.filename)
    owner = request.form.get("owner", "anonymous")
    data = f.read()
    item_id = str(uuid.uuid4())
    filename = f"{item_id}.enc"
    # Encrypt and store
    enc = FERNET.encrypt(data)
    with open(os.path.join(DATA_DIR, filename), "wb") as wf:
        wf.write(enc)
    item = {
        "id": item_id,
        "name": name,
        "size": len(data),
        "bucketKey": filename,
        "ownerId": owner,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "metadata": {},
    }
    items_data["items"].append(item)
    save_items(items_data)
    log_audit(owner, item_id, "upload", True, request.remote_addr)
    return jsonify(
        {"itemId": item_id, "name": name, "size": len(data), "bucketKey": filename}
    )


@APP.route("/download", methods=["GET"])
def download_item():
    if not verify_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    item_id = request.args.get("itemId")
    token = request.args.get("token")
    if not item_id or not token:
        return jsonify({"error": "Missing parameters"}), 400
    payload = verify_token(token)
    if (
        not payload
        or payload.get("dataItemId") != item_id
        or payload.get("scope") != "read"
    ):
        log_audit("unknown", item_id, "download", False, request.remote_addr)
        return jsonify({"error": "Invalid or expired token"}), 403
    # Find item
    item = next((it for it in items_data["items"] if it["id"] == item_id), None)
    if not item:
        log_audit("unknown", item_id, "download", False, request.remote_addr)
        return jsonify({"error": "Item not found"}), 404
    path = os.path.join(DATA_DIR, item["bucketKey"])
    if not os.path.exists(path):
        log_audit(item["ownerId"], item_id, "download", False, request.remote_addr)
        return jsonify({"error": "Stored item not found"}), 500
    with open(path, "rb") as rf:
        enc = rf.read()
    data = FERNET.decrypt(enc)
    log_audit(item["ownerId"], item_id, "download", True, request.remote_addr)
    return send_file(
        io.BytesIO(data),
        as_attachment=True,
        download_name=item["name"],
        mimetype="application/octet-stream",
    )


@APP.route("/share", methods=["POST"])
def share_item():
    if not verify_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(force=True) or {}
    item_id = data.get("itemId")
    expires_in = int(data.get("expiresIn", 3600))
    scope = data.get("scope", "read")
    if not item_id:
        return jsonify({"error": "itemId required"}), 400
    payload = {
        "dataItemId": item_id,
        "expiresAt": int(time.time()) + expires_in,
        "scope": scope,
        "issuedAt": int(time.time()),
    }
    token = sign_token(payload)
    log_audit("system", item_id, "share", True, request.remote_addr)
    return jsonify(
        {
            "token": token,
            "expiresAt": payload["expiresAt"],
            "dataItemId": item_id,
            "scope": scope,
        }
    )


@APP.route("/revoke", methods=["POST"])
def revoke_token():
    # Simple MVP: allow revocation by client providing token to blacklist in memory
    if not verify_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json(force=True) or {}
    token = data.get("token")
    if not token:
        return jsonify({"error": "token required"}), 400
    revoked = request.app.config.setdefault("REVOKED_TOKENS", set())
    revoked.add(token)
    log_audit("system", "unknown", "revoke", True, request.remote_addr)
    return jsonify({"revoked": True})


@APP.route("/logs", methods=["GET"])
def get_logs():
    if not verify_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    item_id = request.args.get("itemId")
    lines = []
    if not os.path.exists(LOG_FILE):
        return jsonify({"logs": []})
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if item_id and line.find(item_id) == -1:
                continue
            lines.append(line.strip())
    return jsonify({"logs": lines})


@APP.before_first_request
def bootstrap():
    APP.config.setdefault("REVOKED_TOKENS", set())


if __name__ == "__main__":
    APP.run(host="0.0.0.0", port=5000)
