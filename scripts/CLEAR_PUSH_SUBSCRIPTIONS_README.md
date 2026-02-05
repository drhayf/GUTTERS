# Clear Push Subscriptions Script

## Overview

This script clears all push notification data from the database, allowing users to re-subscribe with fresh subscriptions after the VAPID fix has been deployed.

## What It Does

1. **Clears all push subscriptions** from the `push_subscriptions` table
2. **Optionally clears notification preferences** from user profiles (with `--clear-preferences` flag)

## When to Use

Use this script **after** deploying the VAPID fix to:
- Clear old/broken push subscriptions that would fail with "BadJwtToken" errors
- Allow users to re-subscribe with the new VAPID keys
- Start fresh with a clean push notification system

## Usage

### Basic Usage (Clear push subscriptions only)
```bash
python scripts/clear_push_subscriptions.py
```

### Clear Both Subscriptions and Preferences
```bash
python scripts/clear_push_subscriptions.py --clear-preferences
```

### Force Delete (Skip Confirmation)
```bash
python scripts/clear_push_subscriptions.py --force
```

### Dry Run (Preview what would be deleted)
```bash
python scripts/clear_push_subscriptions.py --dry-run
```

### Dry Run with Preferences
```bash
python scripts/clear_push_subscriptions.py --clear-preferences --dry-run
```

## Options

| Option | Description |
|---------|-------------|
| `--clear-preferences` | Also clear notification preferences from user profiles |
| `--dry-run` | Show what would be deleted without actually deleting |
| `--force` | Skip confirmation prompt (useful for automation) |

## What Happens After Running

1. **Database is cleaned:** All push subscriptions are deleted
2. **Users need to re-subscribe:** Users will need to enable push notifications again in the app
3. **Fresh start:** New subscriptions will use the fixed VAPID keys

## Safety Features

- **Confirmation required:** You must type "yes" to confirm deletion
- **Dry run mode:** Preview what will be deleted before actually deleting
- **Clear feedback:** Shows exactly what will be deleted

## Example Output

```
======================================================================
CLEAR PUSH SUBSCRIPTIONS
======================================================================

📊 Found 5 push subscription(s) in database

⚠️  WARNING: This will delete ALL push subscriptions!
   Users will need to re-subscribe to push notifications.

   Type 'yes' to confirm deletion: yes

✅ Successfully deleted 5 push subscription(s)

======================================================================
SUMMARY
======================================================================

✅ CLEANUP COMPLETE
   Deleted: 5 push subscription(s)

   Users can now re-subscribe to push notifications

======================================================================
```

## User Communication

After running this script, notify users to re-enable push notifications:

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

### Issue: Script fails with import error
**Solution:** Make sure you're running from the project root directory
```bash
cd c:/dev/GUTTERS
python scripts/clear_push_subscriptions.py
```

### Issue: Database connection error
**Solution:** Verify your `.env` file has correct database credentials

### Issue: No subscriptions found
**Solution:** This is normal if the database is already clean

## Related Files

- **[`src/app/modules/infrastructure/push/service.py`](../src/app/modules/infrastructure/push/service.py)** - Push notification service (now with VAPID fix)
- **[`src/app/core/config.py`](../src/app/core/config.py)** - Configuration with RESOLVED_VAPID_SUB
- **[`VAPID_FIX_SUMMARY.md`](../VAPID_FIX_SUMMARY.md)** - Technical summary of VAPID fix
- **[`VAPID_DEPLOYMENT_CHECKLIST.md`](../VAPID_DEPLOYMENT_CHECKLIST.md)** - Deployment checklist

## Notes

- This script is **safe** to run multiple times
- It only affects push notification data, not user accounts or other data
- Users will need to manually re-enable push notifications in the app
- Consider implementing automatic re-subscription prompt in the app

---

**Created:** 2026-01-28
**Purpose:** Clear push subscriptions after VAPID fix deployment
