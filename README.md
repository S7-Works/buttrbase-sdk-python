# buttrbase

Tiny Python SDK for the [ButtrBase](https://buttrbase.com) API.

## Install

```bash
pip install -e .
```

## Quickstart

### Validate a coupon

```python
from buttrbase import ButtrbaseClient

client = ButtrbaseClient(api_key="your-api-key")
result = client.validate_coupon("SUMMER25", cart_labels=["pro"])
print(result)  # {"valid": True, "discount_cents": 500, ...}
```

### Verify a webhook signature

```python
from buttrbase import webhooks

ok = webhooks.verify_signature(
    body=request_body_bytes,
    signature_header=request.headers["X-Buttrbase-Signature"],
    timestamp_header=request.headers["X-Buttrbase-Timestamp"],
    secret="whsec_...",
)
if not ok:
    raise PermissionError("bad signature")
```

## API reference

```python
ButtrbaseClient(api_key, base_url="https://stagingapi.buttrbase.com", timeout=10.0)

# Coupons
client.validate_coupon(code, cart_labels=None, product_id=None) -> dict

# Gift cards
client.validate_gift_card(code) -> dict
client.redeem_gift_card(code, amount_cents, user_id=None) -> dict

# Magic link
client.send_magic_link(email, org_uuid=None, redirect_to=None) -> dict
client.verify_magic_link(token) -> dict

# MFA
client.mfa_status() -> dict
client.mfa_enroll(label=None) -> dict
client.mfa_activate(code) -> dict

# Org signing
client.org_sign(org_uuid, claims, ttl_seconds=None) -> dict
client.org_jwks(org_uuid) -> dict

# Secrets
client.get_secret(org_uuid, name) -> dict
client.put_secret(org_uuid, name, value, description=None) -> dict
```

Errors are raised as `buttrbase.ButtrbaseError` with `status_code`, `code`, `detail`.

## Docs

See https://buttrbase.com/docs for the full API reference.

## Releasing (maintainers)

Tagged pushes (`v*`) trigger `.github/workflows/release.yml`, which builds and publishes to PyPI via [trusted publishing](https://docs.pypi.org/trusted-publishers/) — no API token required.

One-time setup on PyPI: project Settings → Publishing → Add a new pending publisher:
- Owner: `ButtrBase`
- Repository name: `buttrbase-sdk-python`
- Workflow name: `release.yml`
- Environment name: (leave empty)
