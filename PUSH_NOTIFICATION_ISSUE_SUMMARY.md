# Push Notification Issue - Complete Summary

## Environment
- **Project**: GUTTERS - AI-powered cosmic intelligence system
- **Stack**: Python 3.11+, FastAPI, SQLAlchemy 2.0, PostgreSQL (Supabase), Redis
- **Frontend**: Next.js 14 PWA with Vite
- **Push Library**: `pywebpush` 
- **Hosting**: DevTunnels (HTTPS) for iOS testing

## Database Configuration
- **Production DB**: Supabase PostgreSQL
  - Host: `aws-1-ap-southeast-2.pooler.supabase.com:6543`
  - Database: `postgres`
  - User: `postgres.xrihizuhwdbwbcderbcp`
- **Local DB**: SQLite (`src/sql_app.db`) - not used for production

## VAPID Configuration
Located in `src/.env`:
```
VAPID_PUBLIC_KEY="BEOtLJBw8nrVbimdS2zk-0UBZMaHnrThUsvPLnuGzgc8E49S5Q4Gf2DHoUObgv-2R_oIglh7t7HaXzJbZSmi-8c"
VAPID_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nMIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQg6U7TyxNG6/yD8MIr\nX4IDfkZIzC3+sLN0xVqDA/kU2yehRANCAARDrSyQcPJ61W4pnUts5PtFAWTGh560\n4VLLzy57hs4HPBOPUuUOBn9gx6FDm4L/tkf6CIJYe7ex2l8yW2UpovvH\n-----END PRIVATE KEY-----\n"
VAPID_CLAIM_EMAIL="mailto:admin@gutters.local"
```

## The Problem
iOS Safari Web Push notifications fail with:
```
403 Forbidden - {"reason":"BadAuthorizationHeader"}
```

Push subscription works (200 response), but sending notifications fails.

## What We've Tried

### 1. Manual VAPID Header Generation
- Generated JWT with `sub`, `aud`, `iat`, `exp` claims manually
- Used `cryptography` library to load PEM key and sign JWT
- Passed headers directly to `webpush(..., headers=...)`
- **Issue**: Apple rejected with `BadAuthorizationHeader`

### 2. VAPID Audience Investigation
- **Initial theory**: Wrong `aud` claim for Apple APNs
- **FCM endpoints**: `aud` should be `https://fcm.googleapis.com`
- **Apple endpoints**: `aud` should be the website domain (e.g., `gutters.local`)
- Implemented dynamic audience extraction based on endpoint
- **Result**: Still failed with same error

### 3. pywebpush Built-in VAPID Support
- Switched to `webpush(..., vapid_private_key=..., vapid_claims=...)`
- **Issue**: `Could not deserialize key data. ASN.1 parsing error: invalid length`
- This is a known bug in `pywebpush` with certain EC key formats

### 4. Manifest.json Creation
- Created `frontend/public/manifest.json` (was missing)
- Added `<link rel="manifest">` to `frontend/index.html`
- **Result**: Did not fix the push error

### 5. Subscription Management
- Cleared subscriptions from Supabase (2 subscriptions found and deleted)
- User resubscribed on iOS
- **Result**: Still fails with same errors

### 6. Local VAPID Validation
- Created `scripts/test_vapid_locally.py` to validate VAPID implementation
- All local tests pass:
  - JWT structure correct (`alg: ES256`, `typ: JWT`)
  - Claims correct for both Apple and FCM
  - Public key matches configured key
- **Conclusion**: VAPID code is correct, issue is external

## Current Service State

### `src/app/modules/infrastructure/push/service.py`
Currently using pywebpush built-in VAPID support (fails with key deserialization):
```python
webpush(
    subscription_info={...},
    data=json.dumps(payload),
    vapid_private_key=self.private_key,  # FAILS HERE
    vapid_claims={"sub": settings.RESOLVED_VAPID_SUB},
)
```

The `generate_vapid_headers()` function exists but is not being used.

## Key Files
1. `src/app/modules/infrastructure/push/service.py` - Push service implementation
2. `src/app/core/config.py` - Settings including VAPID config
3. `src/.env` - VAPID keys and database config
4. `frontend/public/manifest.json` - PWA manifest (just created)
5. `frontend/index.html` - Added manifest link
6. `scripts/test_vapid_locally.py` - VAPID validation script
7. `scripts/clear_push_subscriptions.py` - Subscription management

## Known Issues to Investigate

1. **pywebpush EC key parsing bug**: Known issue with certain EC key formats
2. **Apple APNs Web Push requirements**: May have additional validation beyond VAPID spec
3. **Subscription `applicationServerKey`**: The public key used during subscription must match current VAPID key
4. **PWA manifest requirements**: Apple may require specific manifest fields for web push
5. **HTTPS requirements**: Must be served over HTTPS with valid certificate
6. **Service Worker registration**: May need proper SW setup for push

## Suggested Investigation Paths

1. Use a different push library (e.g., `web-push` Node.js alternative, or `python-web-push`)
2. Generate new VAPID keys in different format (try `openssl ecparam` generated keys)
3. Check Apple APNs Web Push documentation for additional requirements
4. Verify the subscription's `applicationServerKey` matches current public key
5. Use a network capture to see exactly what's being sent to Apple
6. Test with a known-working VAPID key pair
7. Check if Apple's push service requires additional headers or different JWT format

## Reproduction Steps
1. Open PWA in iOS Safari
2. Click subscribe button
3. Accept notification permission
4. Call `POST /api/v1/push/test` to send test notification
5. Observe 403 error in server logs

## Current Error Messages
```
# With pywebpush built-in VAPID:
Push error for user 78: Could not deserialize key data. 
The data may be in an incorrect format, it may be encrypted with an unsupported algorithm, 
or it may be an unsupported key type (e.g. EC curves with explicit parameters). 
Details: ASN.1 parsing error: invalid length

# With manual headers (before):
Push failed for user 78 (https://web.push.apple.com/...): 
WebPushException: Push failed: 403 Forbidden
Response body:{"reason":"BadAuthorizationHeader"}
```

---

**Goal**: Get iOS Safari Web Push notifications working reliably without 403 errors.
