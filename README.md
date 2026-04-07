-# Secure Cloud Data Sharing (MVP)

Unified MVP overview (single plan)
- This project demonstrates a provider-agnostic, free-path MVP for secure file storage and sharing.
- It uses local storage by default to simulate a cloud environment and can switch to AWS S3 if credentials are provided.
- Key features included: encrypted storage, IAM-like access via API key, token-based sharing, and persistent audit logs.
- The MVP is designed for a college project demo with a clean, reproducible workflow.

What you will get
- Encrypted data storage (local Fernet-based encryption) for uploaded files
- Access control management via an API key header (IAM-like gate)
- Secure sharing mechanism using expiring, tamper-evident tokens
- Audit logs captured to a cloud-like sink (audit.log) for visibility
- A provider-agnostic storage backend (default local; optional AWS S3)

How to run locally (free-path by default)
- Prerequisites
  - Python 3.8+
  - Optional virtual environment (recommended)
  - Environment variables (recommended):
    API_KEY: your chosen API key for requests
    CLOUD_PROVIDER: local (default) or aws
    AWS_S3_BUCKET: required if CLOUD_PROVIDER=aws
    LOCAL_STORAGE_DIR: optional base dir for local storage (default: data/)
    TOKEN_SIGNING_SECRET: secret used for signing tokens

- Step-by-step
  1) Install dependencies
     python -m venv venv
     source venv/bin/activate  # macOS/Linux
     .\venv\Scripts\activate   # Windows
     pip install -r secure_share/requirements.txt
  2) Run the server (insecure by default for local testing)
     python secure_share/app.py
     The API will listen on http://0.0.0.0:5000 by default

- How to use (curl examples)
  1) Upload a file
     curl -X POST http://localhost:5000/upload \
       -F "file=@/path/to/file.txt" \
       -F "name=file.txt" \
       -F "owner=student" \
       -H "X-API-KEY: your-api-key"
  2) Create a share token
     curl -X POST http://localhost:5000/share \
       -H "Content-Type: application/json" \
       -H "X-API-KEY: your-api-key" \
       -d '{"itemId":"<ITEM_ID>","expiresIn":3600,"scope":"read"}'
  3) Download with token
     curl -L "http://localhost:5000/download?itemId=<ITEM_ID>&token=<TOKEN>"
  4) View logs
     curl -H "X-API-KEY: your-api-key" "http://localhost:5000/logs?itemId=<ITEM_ID>"

- How the data flows (end-to-end)
  1) Upload: a file is uploaded, encrypted, and stored in storage backend.
  2) Share: a short-lived, signed token is generated for the item.
  3) Access: the recipient uses the token to download; token expiry and scope are checked.
  4) Audit: each action (upload, share, access) is logged for traceability.

API Reference (MVP)
- POST /upload
- GET /download?itemId=&token=
- POST /share
- POST /revoke
- GET /logs?itemId=

Security and compliance (MVP)
- Encryption at rest with a Fernet key (local for MVP; switch to KMS in cloud)
- TLS in transit is assumed for demo; enable TLS in production
- Access control through an API key header (X-API-KEY)
- Tokens are signed with HMAC for integrity and expiry control
- Audit logs stored in audit.log (local) or cloud logging sink in a production setup

Notes
- Revocation is implemented as a persisted blacklist for demonstration purposes.
- This MVP is designed for a classroom setting and not production-ready; replace with cloud-native services for a real deployment.

Contributing
- If you want to contribute, please follow the plan in UNIFIED_PLAN.md and add tests and docs.

- Encrypted data storage (local Fernet-based) representing cloud storage with KMS-like keys
- Access control via API key (IAM-like)
- Secure sharing via expiring tokens / signed URLs
- Audit logs captured to a cloud-like sink (audit.log)
- Single-region deployment with a free-path provider

Where to look
- UNIFIED_PLAN.md contains the consolidated plan and demo steps
- secure_share/app.py is the main API server for the MVP
- secure_share/README.md contains quick usage notes and demo flow
