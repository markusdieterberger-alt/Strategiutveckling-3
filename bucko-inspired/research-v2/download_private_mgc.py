#!/usr/bin/env python3
"""Download private canonical MGC dataset from Google Drive using a least-privileged service account.

Credentials are supplied by google-github-actions/auth via GOOGLE_APPLICATION_CREDENTIALS.
The service account must be explicitly shared as Viewer on the single Drive file.
Never print credentials or request public-link sharing.
"""
import hashlib
import os
import sys
from pathlib import Path

import google.auth
from google.auth.transport.requests import AuthorizedSession

FILE_ID = "1mezHKoBtkIlDt72ec81QXEORtHdCNiCG"
SHA256 = "fc7c9493a9a50301d14e665f8ae99234e591fcef70deebdf65c5f9d61e3b01d0"
TARGET = Path("data/MGC_CANONICAL_1M_V1_0_2026-10-05.csv.gz")

def main():
    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/drive.readonly"])
    session = AuthorizedSession(credentials)
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    url = f"https://www.googleapis.com/drive/v3/files/{FILE_ID}"
    try:
        with session.get(url, params={"alt": "media", "supportsAllDrives": "true"},
                         stream=True, timeout=(30, 120)) as response:
            if response.status_code in (403, 404):
                raise RuntimeError(
                    f"Drive HTTP {response.status_code}: Verify that the service-account email "
                    "has Viewer permission on the individual MGC file and that Drive API is enabled. "
                    "Keep the file private; do not enable public-link access."
                )
            response.raise_for_status()
            sha = hashlib.sha256()
            total = 0
            with TARGET.open("wb") as fout:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        fout.write(chunk)
                        sha.update(chunk)
                        total += len(chunk)
    except Exception:
        TARGET.unlink(missing_ok=True)
        raise
    if sha.hexdigest() != SHA256:
        TARGET.unlink(missing_ok=True)
        raise RuntimeError("Dataset SHA256 mismatch; rejected. Check that the original compressed canonical file was shared.")
    print(f"Private Drive download verified: {total} bytes, SHA256={sha.hexdigest()}")

if __name__ == "__main__":
    main()
