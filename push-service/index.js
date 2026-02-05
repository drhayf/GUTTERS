/**
 * GUTTERS Push Notification Microservice
 * 
 * Node.js service for Web Push notifications using the proven web-push library.
 * Integrates with Python backend via HTTP API with token authentication.
 */

require('dotenv').config();
const express = require('express');
const webPush = require('web-push');
const cors = require('cors');
const helmet = require('helmet');

const app = express();
const PORT = process.env.PORT || 4000;

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json());

// Configure VAPID
if (process.env.VAPID_PUBLIC_KEY && process.env.VAPID_PRIVATE_KEY) {
    webPush.setVapidDetails(
        process.env.VAPID_SUBJECT || 'mailto:admin@gutters.local',
        process.env.VAPID_PUBLIC_KEY,
        process.env.VAPID_PRIVATE_KEY
    );
    console.log('✅ VAPID configured successfully');
} else {
    console.error('❌ VAPID keys not configured!');
    process.exit(1);
}

// Auth middleware
const authMiddleware = (req, res, next) => {
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return res.status(401).json({ error: 'Missing authorization header' });
    }

    const token = authHeader.substring(7);

    if (token !== process.env.AUTH_TOKEN) {
        return res.status(403).json({ error: 'Invalid auth token' });
    }

    next();
};

// Health check
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        service: 'gutters-push-service',
        vapid_configured: !!process.env.VAPID_PUBLIC_KEY
    });
});

// Send notification to single subscription
app.post('/send', authMiddleware, async (req, res) => {
    try {
        const { subscription, payload } = req.body;

        if (!subscription || !subscription.endpoint) {
            return res.status(400).json({ error: 'Missing subscription data' });
        }

        if (!payload || !payload.title) {
            return res.status(400).json({ error: 'Missing payload data' });
        }

        const notificationPayload = JSON.stringify({
            title: payload.title,
            body: payload.body || '',
            url: payload.url || '/',
            icon: payload.icon || '/icons/icon-192.png',
        });

        await webPush.sendNotification(subscription, notificationPayload);

        res.json({
            success: true,
            message: 'Notification sent successfully'
        });

    } catch (error) {
        console.error('Push error:', error);

        if (error.statusCode === 410) {
            return res.status(410).json({
                success: false,
                error: 'Subscription expired',
                statusCode: 410
            });
        }

        if (error.statusCode === 404) {
            return res.status(404).json({
                success: false,
                error: 'Subscription not found',
                statusCode: 404
            });
        }

        res.status(500).json({
            success: false,
            error: error.message || 'Failed to send notification',
            statusCode: error.statusCode || 500
        });
    }
});

// Send notification to multiple subscriptions
app.post('/send-batch', authMiddleware, async (req, res) => {
    try {
        const { subscriptions, payload } = req.body;

        if (!Array.isArray(subscriptions) || subscriptions.length === 0) {
            return res.status(400).json({ error: 'Invalid subscriptions array' });
        }

        if (!payload || !payload.title) {
            return res.status(400).json({ error: 'Missing payload data' });
        }

        const notificationPayload = JSON.stringify({
            title: payload.title,
            body: payload.body || '',
            url: payload.url || '/',
            icon: payload.icon || '/icons/icon-192.png',
        });

        const results = {
            success: 0,
            failed: 0,
            expired: 0,
            errors: []
        };

        for (const subscription of subscriptions) {
            try {
                await webPush.sendNotification(subscription, notificationPayload);
                results.success++;
            } catch (error) {
                if (error.statusCode === 410 || error.statusCode === 404) {
                    results.expired++;
                } else {
                    results.failed++;
                    results.errors.push({
                        endpoint: subscription.endpoint?.substring(0, 50) + '...',
                        error: error.message,
                        statusCode: error.statusCode
                    });
                }
            }
        }

        res.json({
            success: true,
            results
        });

    } catch (error) {
        console.error('Batch push error:', error);
        res.status(500).json({
            success: false,
            error: error.message || 'Failed to send batch notifications'
        });
    }
});

// Get VAPID public key
app.get('/vapid-public-key', (req, res) => {
    res.json({
        publicKey: process.env.VAPID_PUBLIC_KEY
    });
});

// Start server
app.listen(PORT, () => {
    console.log(`🚀 Push service running on port ${PORT}`);
    console.log(`📡 Endpoints:`);
    console.log(`   GET  /health              - Health check`);
    console.log(`   GET  /vapid-public-key    - Get VAPID public key`);
    console.log(`   POST /send                - Send single notification (auth required)`);
    console.log(`   POST /send-batch          - Send batch notifications (auth required)`);
});
