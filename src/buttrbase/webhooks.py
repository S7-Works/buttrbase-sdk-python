"""Webhook signature verification for ButtrBase events."""
from __future__ import annotations

import hashlib
import hmac
import time


def _constant_time_eq(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def compute_signature(body: bytes, timestamp: str, secret: str) -> str:
    """Compute the hex HMAC-SHA256 signature over `<timestamp>.<body>`."""
    mac = hmac.new(
        secret.encode("utf-8"),
        msg=f"{timestamp}.".encode("utf-8") + body,
        digestmod=hashlib.sha256,
    )
    return mac.hexdigest()


def verify_signature(
    body: bytes,
    signature_header: str,
    timestamp_header: str,
    secret: str,
    tolerance_seconds: int = 300,
) -> bool:
    """Verify a ButtrBase webhook signature.

    Returns True iff the HMAC-SHA256 of `<timestamp>.<body>` matches
    `signature_header` (hex) and the timestamp is within tolerance.
    """
    if not signature_header or not timestamp_header or not secret:
        return False
    try:
        ts = int(timestamp_header)
    except (TypeError, ValueError):
        return False
    if abs(time.time() - ts) > tolerance_seconds:
        return False
    expected = compute_signature(body, timestamp_header, secret)
    sig = signature_header.strip()
    if sig.startswith("sha256="):
        sig = sig[len("sha256=") :]
    return _constant_time_eq(expected, sig)
