# GUTTERS Push Notification Microservice

Node.js microservice for Web Push notifications using the industry-standard `web-push` library.

## Why This Exists

Python's `pywebpush` library has compatibility issues with Apple APNs Web Push. This Node.js service uses the proven `web-push` library (same as barbbarb project) which works reliably with:
- ✅ Apple APNs Web Push (iOS Safari)
- ✅ Google FCM (Android Chrome)
- ✅ Mozilla Push (Firefox)

## Setup

### 1. Install Dependencies
```bash
cd push-service
npm install
```

### 2. Configure Environment
Copy `.env.example` to `.env` and update:
```bash
cp .env.example .env
```

**Important:** Make sure VAPID keys match your Python backend (`../src/.env`)

### 3. Start Service
```bash
# Development (with auto-reload)
npm run dev

# Production
npm start
```

The service will run on `http://localhost:4000`

## API Endpoints

### Health Check
```bash
GET /health
```

Returns service status and configuration.

### Get VAPID Public Key
```bash
GET /vapid-public-key
```

Returns the VAPID public key for client-side subscription.

### Send Single Notification
```bash
POST /send
Authorization: Bearer <AUTH_TOKEN>
Content-Type: application/json

{
  "subscription": {
    "endpoint": "https://web.push.apple.com/...",
    "keys": {
      "p256dh": "BOf...",
      "auth": "66sG..."
    }
  },
  "payload": {
    "title": "Notification Title",
    "body": "Notification body text",
    "url": "/dashboard",
    "icon": "/icon.png"
  }
}
```

### Send Batch Notifications
```bash
POST /send-batch
Authorization: Bearer <AUTH_TOKEN>
Content-Type: application/json

{
  "subscriptions": [
    {
      "endpoint": "https://web.push.apple.com/...",
      "keys": { "p256dh": "...", "auth": "..." }
    }
  ],
  "payload": {
    "title": "Batch Notification",
    "body": "Sent to multiple devices"
  }
}
```

## Integration with Python Backend

The Python backend (`../src/app/modules/infrastructure/push/service.py`) automatically calls this service.

### Authentication

The service uses token-based authentication. Make sure these match:
- **Node.js:** `AUTH_TOKEN` in `push-service/.env`
- **Python:** `PUSH_SERVICE_TOKEN` in `src/app/modules/infrastructure/push/service.py`

### Starting Both Services

```bash
# Terminal 1: Start Node.js push service
cd push-service
npm start

# Terminal 2: Start Python backend
cd ..
# Your normal Python startup command
```

## Security

- ✅ Token-based authentication for all endpoints
- ✅ CORS configured for local development
- ✅ Helmet.js for security headers
- ✅ Rate limiting recommended for production

## Production Deployment

### Option 1: PM2 (Recommended)
```bash
npm install -g pm2
pm2 start index.js --name gutters-push
pm2 save
pm2 startup
```

### Option 2: Systemd Service
Create `/etc/systemd/system/gutters-push.service`:
```ini
[Unit]
Description=GUTTERS Push Service
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/GUTTERS/push-service
ExecStart=/usr/bin/node index.js
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable gutters-push
sudo systemctl start gutters-push
```

## Monitoring

Check service health:
```bash
curl http://localhost:4000/health
```

View logs (PM2):
```bash
pm2 logs gutters-push
```

## Troubleshooting

### "Cannot connect to push service"
- Make sure Node.js service is running: `npm start`
- Check port 4000 is not in use
- Verify `PUSH_SERVICE_URL` in Python matches Node.js PORT

### "Invalid auth token"
- Ensure `AUTH_TOKEN` in `.env` matches Python's `PUSH_SERVICE_TOKEN`
- Check Authorization header format: `Bearer <token>`

### "VAPID keys not configured"
- Copy VAPID keys from `../src/.env` to `push-service/.env`
- Ensure private key includes `-----BEGIN PRIVATE KEY-----` markers

## Architecture

```
┌─────────────────┐
│  Python Backend │
│   (FastAPI)     │
└────────┬────────┘
         │ HTTP POST
         │ (with auth token)
         ▼
┌─────────────────┐
│ Node.js Service │
│   (Express)     │
│  + web-push lib │
└────────┬────────┘
         │ HTTPS POST
         │ (with VAPID)
         ▼
┌─────────────────┐
│  Apple APNs     │
│  FCM / Mozilla  │
└─────────────────┘
```

## License

MIT - Same as GUTTERS project
