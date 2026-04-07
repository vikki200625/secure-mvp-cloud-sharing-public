#!/usr/bin/env python3
import os
import time
import io
import requests

BASE_URL = os.environ.get("BASE_URL", "http://localhost:5000")
API_KEY = os.environ.get("API_KEY", "demo-key")


def api_headers():
    return {"X-API-KEY": API_KEY}


def main():
    # Create a tiny test file in memory and upload it
    filename = "demo.txt"
    content = b"Hello, secure world!"
    files = {"file": (io.BytesIO(content), filename)}
    data = {"name": filename, "owner": "demo"}
    r = requests.post(
        f"{BASE_URL}/upload", files=files, data=data, headers=api_headers()
    )
    if r.status_code != 200:
        print("Upload failed:", r.status_code, r.text)
        return
    item_id = r.json().get("itemId")
    print("Uploaded item_id=", item_id)

    # Create share token
    payload = {"itemId": item_id, "expiresIn": 60, "scope": "read"}
    r = requests.post(f"{BASE_URL}/share", json=payload, headers=api_headers())
    if r.status_code != 200:
        print("Share failed:", r.status_code, r.text)
        return
    token = r.json().get("token")
    print("Share token:", token)

    # Download using token
    r = requests.get(
        f"{BASE_URL}/download?itemId={item_id}&token={token}",
        headers=api_headers(),
        stream=True,
    )
    if r.status_code != 200:
        print("Download failed:", r.status_code, r.text)
        return
    # Consume content
    data = r.content
    print("Downloaded data length:", len(data))

    # View logs
    r = requests.get(f"{BASE_URL}/logs?itemId={item_id}", headers=api_headers())
    print("Logs status:", r.status_code)
    print(r.text[:300] + "" if r.text else "")


if __name__ == "__main__":
    main()
