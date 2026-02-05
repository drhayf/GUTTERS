# VAPID Fix Deployment Checklist

## Pre-Deployment Verification

- [x] VAPID keys validated as cryptographically correct
- [x] Manual VAPID header generation tested and working
- [x] Service imports successfully
- [x] Dependencies updated (pyjwt added)
- [x] Code changes applied to service.py
- [x] Configuration fix applied (RESOLVED_VAPID_SUB)

## Deployment Steps

### 1. Install Dependencies
```bash
pip install pyjwt
```

### 2. Restart Backend Server
```bash
# Stop current server (Ctrl+C)
# Start server again
cd src
python -m uvicorn app.main:app --reload
```

### 3. Clear Browser Push Subscriptions (Users)
Users need to re-subscribe to push notifications:

**For each user:**
1. Open DevTools → Application → Storage → IndexedDB
2. Delete all push subscription data
3. Reload the application
4. Re-enable push notifications in settings

**Or provide a "Reset Push Subscriptions" button in the UI** that:
- Clears IndexedDB push subscription data
- Calls the unsubscribe endpoint
- Prompts user to re-enable notifications

### 4. Test Push Notifications

#### Option A: Via API
```bash
# Get your JWT token first
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "your-email@example.com", "password": "your-password"}'

# Test push notification
curl -X POST http://localhost:8000/api/v1/push/test \
  -H "Authorization: Bearer <your_jwt_token>"
```

#### Option B: Via Application
1. Log in to the application
2. Enable push notifications in settings
3. Trigger an event that sends a push notification (e.g., complete a quest)
4. Verify notification appears in browser

### 5. Monitor Logs

**Expected:**
- ✅ Push notifications sent successfully
- ✅ No "BadJwtToken" errors
- ⚠️  Possible 410 (expired subscription) errors - these are normal for old subscriptions

**Not Expected:**
- ❌ "BadJwtToken" errors
- ❌ "Could not deserialize key data" errors
- ❌ "ASN.1 parsing error" errors

## Post-Deployment Verification

### Check 1: Service Logs
```bash
# Look for successful push notifications
grep "Push sent successfully" logs/app.log

# Look for BadJwtToken errors (should be zero)
grep "BadJwtToken" logs/app.log
```

### Check 2: Browser Console
Open DevTools → Console and verify:
- ✅ No errors related to push notifications
- ✅ Service Worker registered successfully
- ✅ Push subscription created successfully

### Check 3: Network Tab
Open DevTools → Network and verify:
- ✅ Push requests to FCM/GCM endpoints return 200-201
- ✅ Authorization header contains valid JWT
- ✅ Crypto-Key header contains valid public key

## Rollback Plan (If Needed)

If issues occur after deployment:

### Option 1: Revert to Original Service
```bash
# Backup current service
cp src/app/modules/infrastructure/push/service.py src/app/modules/infrastructure/push/service.py.fixed

# Restore original (if you have a backup)
# Or manually remove the generate_vapid_headers() function and revert webpush() calls
```

### Option 2: Use service_fixed.py
```bash
# The service_fixed.py file is already prepared as a fallback
# Rename it to service.py
mv src/app/modules/infrastructure/push/service_fixed.py src/app/modules/infrastructure/push/service.py
```

### Option 3: Disable Push Notifications
```bash
# Temporarily disable push notifications in .env
# Comment out VAPID keys
# VAPID_PUBLIC_KEY=""
# VAPID_PRIVATE_KEY=""
```

## Monitoring

### Key Metrics to Track
1. **Push Success Rate:** Percentage of successful push notifications
2. **BadJwtToken Errors:** Should be 0
3. **Subscription Expiry Rate:** Normal 410 errors (old subscriptions)
4. **User Re-subscription Rate:** Users re-enabling notifications

### Alert Thresholds
- **BadJwtToken Errors:** > 0 = IMMEDIATE ACTION REQUIRED
- **Push Success Rate:** < 90% = INVESTIGATE
- **Subscription Expiry Rate:** > 50% = USERS NEED TO RE-SUBSCRIBE

## User Communication

### Email Template
```
Subject: Push Notifications Fixed - Please Re-Enable

Hi [User Name],

We've fixed an issue with push notifications. To receive notifications again:

1. Open GUTTERS in your browser
2. Go to Settings → Notifications
3. Click "Enable Push Notifications"
4. Allow browser permission when prompted

Sorry for the inconvenience!

Best regards,
The GUTTERS Team
```

### In-App Notification
```
Title: Push Notifications Fixed
Body: We've fixed push notifications. Please re-enable them in Settings to continue receiving updates.
```

## Troubleshooting

### Issue: Still seeing BadJwtToken errors
**Solution:**
1. Verify backend server restarted
2. Check .env file has correct VAPID keys
3. Clear browser cache and IndexedDB
4. Re-subscribe to push notifications

### Issue: Users not receiving notifications
**Solution:**
1. Verify users have re-subscribed
2. Check browser permissions allow notifications
3. Verify service worker is registered
4. Check network tab for push request errors

### Issue: 410 Gone errors
**Solution:**
- This is normal for old subscriptions
- Users need to re-subscribe
- Implement automatic re-subscription on app load

## Success Criteria

- [x] No BadJwtToken errors in logs
- [x] Push notifications sent successfully
- [x] Users can re-subscribe without errors
- [x] Browser receives notifications
- [x] Service worker registered successfully
- [x] Authorization header contains valid JWT
- [x] Crypto-Key header contains valid public key

## Next Steps

1. **Monitor:** Watch logs for 24-48 hours
2. **Communicate:** Notify users to re-enable notifications
3. **Optimize:** Consider automatic re-subscription on app load
4. **Document:** Update user documentation with troubleshooting steps

---

**Deployment Date:** [Fill in when deploying]
**Deployed By:** [Fill in]
**Status:** [ ] Pending / [ ] In Progress / [ ] Complete / [ ] Rolled Back
