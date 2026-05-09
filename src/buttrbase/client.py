"""ButtrBase API client."""
from __future__ import annotations

from typing import Any, Optional

import requests

from .errors import ButtrbaseError

DEFAULT_BASE_URL = "https://stagingapi.buttrbase.com"


class ButtrbaseClient:
    """Small synchronous client for the ButtrBase API."""

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 10.0,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()

    # ----- internal -----
    def _headers(self, auth: bool = True) -> dict:
        h = {"Accept": "application/json", "Content-Type": "application/json"}
        if auth and self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[dict] = None,
        params: Optional[dict] = None,
        auth: bool = True,
    ) -> Any:
        url = f"{self.base_url}{path}"
        resp = self._session.request(
            method,
            url,
            json=json,
            params=params,
            headers=self._headers(auth=auth),
            timeout=self.timeout,
        )
        return self._handle(resp)

    @staticmethod
    def _handle(resp: requests.Response) -> Any:
        try:
            body = resp.json() if resp.content else None
        except ValueError:
            body = None
        if 200 <= resp.status_code < 300:
            return body if body is not None else {}
        code = None
        detail: Any = body
        message = f"HTTP {resp.status_code}"
        if isinstance(body, dict):
            code = body.get("code") or body.get("error")
            detail = body.get("detail", body.get("message", body))
            message = str(body.get("message") or body.get("error") or message)
        raise ButtrbaseError(
            message, status_code=resp.status_code, code=code, detail=detail
        )

    # ----- Coupons -----
    def validate_coupon(
        self,
        code: str,
        cart_labels: Optional[list[str]] = None,
        product_id: Optional[int] = None,
    ) -> dict:
        payload: dict = {"code": code}
        if cart_labels is not None:
            payload["cart_labels"] = cart_labels
        if product_id is not None:
            payload["product_id"] = product_id
        return self._request("POST", "/api/v1/coupons/validate", json=payload, auth=False)

    # ----- Gift cards -----
    def validate_gift_card(self, code: str) -> dict:
        return self._request(
            "POST", "/api/v1/gift-cards/validate", json={"code": code}, auth=False
        )

    def redeem_gift_card(
        self, code: str, amount_cents: int, user_id: Optional[int] = None
    ) -> dict:
        payload: dict = {"code": code, "amount_cents": amount_cents}
        if user_id is not None:
            payload["user_id"] = user_id
        return self._request("POST", "/api/v1/gift-cards/redeem", json=payload)

    # ----- Magic link -----
    def send_magic_link(
        self,
        email: str,
        org_uuid: Optional[str] = None,
        redirect_to: Optional[str] = None,
    ) -> dict:
        payload: dict = {"email": email}
        if org_uuid is not None:
            payload["org_uuid"] = org_uuid
        if redirect_to is not None:
            payload["redirect_to"] = redirect_to
        return self._request("POST", "/api/v1/auth/magic-link/send", json=payload, auth=False)

    def verify_magic_link(self, token: str) -> dict:
        return self._request(
            "POST", "/api/v1/auth/magic-link/verify", json={"token": token}, auth=False
        )

    # ----- MFA -----
    def mfa_status(self) -> dict:
        return self._request("GET", "/api/v1/auth/mfa/status")

    def mfa_enroll(self, label: Optional[str] = None) -> dict:
        payload: dict = {}
        if label is not None:
            payload["label"] = label
        return self._request("POST", "/api/v1/auth/mfa/enroll", json=payload)

    def mfa_activate(self, code: str) -> dict:
        return self._request("POST", "/api/v1/auth/mfa/activate", json={"code": code})

    # ----- Org signing -----
    def org_sign(
        self, org_uuid: str, claims: dict, ttl_seconds: Optional[int] = None
    ) -> dict:
        payload: dict = {"claims": claims}
        if ttl_seconds is not None:
            payload["ttl_seconds"] = ttl_seconds
        return self._request("POST", f"/api/v1/orgs/{org_uuid}/sign", json=payload)

    def org_jwks(self, org_uuid: str) -> dict:
        return self._request(
            "GET", f"/api/v1/orgs/{org_uuid}/.well-known/jwks.json", auth=False
        )

    # ----- Secrets -----
    def get_secret(self, org_uuid: str, name: str) -> dict:
        return self._request("GET", f"/api/v1/orgs/{org_uuid}/secrets/{name}")

    def put_secret(
        self,
        org_uuid: str,
        name: str,
        value: str,
        description: Optional[str] = None,
    ) -> dict:
        payload: dict = {"value": value}
        if description is not None:
            payload["description"] = description
        return self._request(
            "PUT", f"/api/v1/orgs/{org_uuid}/secrets/{name}", json=payload
        )

    # ----- Step-up auth -----
    def auth_step_up(self, code: str, recovery: bool = False) -> dict:
        """POST /api/auth/step-up.

        Exchange an MFA TOTP (or recovery) code for a short-lived
        elevated access token (~5 min). On success the SDK's bearer
        token is REPLACED with the returned ``access_token`` so the
        next admin / JIT call carries the elevated session.
        """
        payload = {"code": code, "recovery": recovery}
        body = self._request("POST", "/api/auth/step-up", json=payload)
        if isinstance(body, dict) and body.get("access_token"):
            self.api_key = body["access_token"]
        return body

    # ----- JIT elevation (admin) -----
    # All elevation endpoints require an active step-up session.
    def elevation_request(
        self,
        org_uuid: str,
        scope: str,
        reason: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
    ) -> dict:
        """POST /api/admin/orgs/{org_uuid}/elevation/request — returns a grant view."""
        payload: dict = {"scope": scope}
        if reason is not None:
            payload["reason"] = reason
        if ttl_seconds is not None:
            payload["ttl_seconds"] = ttl_seconds
        return self._request(
            "POST", f"/api/admin/orgs/{org_uuid}/elevation/request", json=payload
        )

    def elevation_approve(self, org_uuid: str, grant_uuid: str) -> dict:
        """POST /api/admin/orgs/{org_uuid}/elevation/{grant_uuid}/approve.

        Server returns 403 if the approver is the same admin as the requester.
        """
        return self._request(
            "POST",
            f"/api/admin/orgs/{org_uuid}/elevation/{grant_uuid}/approve",
        )

    def elevation_list(self, org_uuid: str, status: Optional[str] = None) -> list:
        """GET /api/admin/orgs/{org_uuid}/elevation — list grant views."""
        params: dict = {}
        if status is not None:
            params["status"] = status
        return self._request(
            "GET",
            f"/api/admin/orgs/{org_uuid}/elevation",
            params=params or None,
        )

    # ----- SPIFFE -----
    def spiffe_issue_svid(
        self,
        org_uuid: str,
        workload_path: str,
        ttl_seconds: Optional[int] = None,
    ) -> dict:
        """POST /api/admin/orgs/{org_uuid}/spiffe/svid — issue an X.509 SVID."""
        payload: dict = {"workload_path": workload_path}
        if ttl_seconds is not None:
            payload["ttl_seconds"] = ttl_seconds
        return self._request(
            "POST", f"/api/admin/orgs/{org_uuid}/spiffe/svid", json=payload
        )

    # ----- Context-aware auth events -----
    def list_auth_events(
        self,
        org_uuid: str,
        user_uuid: Optional[str] = None,
        limit: int = 50,
    ) -> list:
        """GET /api/admin/orgs/{org_uuid}/auth-events."""
        params: dict = {"limit": limit}
        if user_uuid is not None:
            params["user_uuid"] = user_uuid
        return self._request(
            "GET", f"/api/admin/orgs/{org_uuid}/auth-events", params=params
        )

    # ----- Re-encrypt (key rotation) -----
    def reencrypt_secrets(self, org_uuid: str) -> dict:
        """POST /api/admin/orgs/{org_uuid}/reencrypt/secrets."""
        return self._request(
            "POST", f"/api/admin/orgs/{org_uuid}/reencrypt/secrets"
        )

    def reencrypt_signing_keys(self, org_uuid: str) -> dict:
        """POST /api/admin/orgs/{org_uuid}/reencrypt/signing-keys."""
        return self._request(
            "POST", f"/api/admin/orgs/{org_uuid}/reencrypt/signing-keys"
        )

    def reencrypt_mtls_ca(self, org_uuid: str) -> dict:
        """POST /api/admin/orgs/{org_uuid}/reencrypt/mtls-ca."""
        return self._request(
            "POST", f"/api/admin/orgs/{org_uuid}/reencrypt/mtls-ca"
        )

    # ----- Sessions -----
    def revoke_session(self, jti: str, ttl_seconds: Optional[int] = None) -> dict:
        """POST /api/admin/sessions/revoke — add ``jti`` to the revocation list."""
        payload: dict = {"jti": jti}
        if ttl_seconds is not None:
            payload["ttl_seconds"] = ttl_seconds
        return self._request("POST", "/api/admin/sessions/revoke", json=payload)

    # ----- Metrics -----
    def get_org_metrics(self, org_uuid: str) -> dict:
        """GET /api/admin/orgs/{org_uuid}/metrics."""
        return self._request("GET", f"/api/admin/orgs/{org_uuid}/metrics")
