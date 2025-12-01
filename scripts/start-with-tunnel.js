const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const http = require('http');

const FASTAPI_PORT = 8000;
const ENV_FILE = path.join(__dirname, '..', '.env');

function updateEnvFile(apiUrl) {
  let envContent = fs.readFileSync(ENV_FILE, 'utf8');
  
  // Update or add EXPO_PUBLIC_API_URL
  if (envContent.match(/^EXPO_PUBLIC_API_URL=/m)) {
    envContent = envContent.replace(
      /^EXPO_PUBLIC_API_URL=.*/m,
      `EXPO_PUBLIC_API_URL=${apiUrl}`
    );
  } else {
    // Add after the comment block about API URL
    envContent = envContent.replace(
      /# EXPO_PUBLIC_API_URL=.*/,
      `# EXPO_PUBLIC_API_URL=https://xxx-8000.aue.devtunnels.ms\nEXPO_PUBLIC_API_URL=${apiUrl}`
    );
  }
  
  fs.writeFileSync(ENV_FILE, envContent);
  console.log(`📝 Updated .env with: EXPO_PUBLIC_API_URL=${apiUrl}`);
}

async function getTunnelUrl() {
  // Query ngrok's local API to get the public URL
  return new Promise((resolve, reject) => {
    const req = http.get('http://127.0.0.1:4040/api/tunnels', (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const tunnels = JSON.parse(data);
          const httpsTunnel = tunnels.tunnels.find(t => t.proto === 'https');
          resolve(httpsTunnel ? httpsTunnel.public_url : null);
        } catch (e) {
          reject(e);
        }
      });
    });
    req.on('error', reject);
    req.setTimeout(5000, () => {
      req.destroy();
      reject(new Error('Timeout'));
    });
  });
}

async function startTunnel() {
  return new Promise(async (resolve) => {
    console.log('🚇 Starting ngrok tunnel for FastAPI...');
    
    // Start ngrok as a background process
    const ngrokProcess = spawn('ngrok', ['http', String(FASTAPI_PORT)], {
      stdio: 'ignore',
      detached: true,
      shell: true,
    });
    ngrokProcess.unref();
    
    // Wait for ngrok to start and get the URL
    let attempts = 0;
    const maxAttempts = 10;
    
    while (attempts < maxAttempts) {
      await new Promise(r => setTimeout(r, 1000));
      try {
        const url = await getTunnelUrl();
        if (url) {
          console.log(`🌐 ngrok tunnel: ${url}`);
          resolve(url);
          return;
        }
      } catch (e) {
        // ngrok not ready yet
      }
      attempts++;
    }
    
    console.error('❌ Failed to get ngrok tunnel URL after 10 seconds');
    console.log('⚠️  Mobile API calls may not work. Continuing anyway...\n');
    resolve(null);
  });
}

async function main() {
  // Start ngrok tunnel first
  const tunnelUrl = await startTunnel();
  
  if (tunnelUrl) {
    // Write to .env file - Metro reads this at bundle time
    updateEnvFile(tunnelUrl);
  }
  
  console.log(`\n✅ API URL: ${tunnelUrl || 'localhost (no tunnel)'}\n`);
  
  // Start FastAPI
  console.log('🐍 Starting FastAPI server...');
  const api = spawn('.venv\\Scripts\\python.exe', ['apps/api/main.py'], {
    stdio: 'inherit',
    shell: true,
  });
  
  // Wait a moment for API to start
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  // Start Expo with --clear to ensure fresh bundle with new env var
  console.log('📱 Starting Expo (with cache clear to pick up new API URL)...');
  const expo = spawn('npx', ['expo', 'start', '--tunnel', '--clear'], {
    stdio: 'inherit',
    shell: true,
  });
  
  // Handle cleanup
  const cleanup = async () => {
    console.log('\n🧹 Cleaning up...');
    try {
      // Kill ngrok process
      if (process.platform === 'win32') {
        execSync('taskkill /F /IM ngrok.exe 2>nul', { stdio: 'ignore' });
      } else {
        execSync('pkill -f ngrok', { stdio: 'ignore' });
      }
    } catch (e) {}
    api.kill();
    expo.kill();
    process.exit(0);
  };
  
  process.on('SIGINT', cleanup);
  process.on('SIGTERM', cleanup);
  
  // Wait for processes
  api.on('close', (code) => {
    console.log(`API exited with code ${code}`);
  });
  
  expo.on('close', (code) => {
    console.log(`Expo exited with code ${code}`);
    cleanup();
  });
}

main().catch(console.error);
