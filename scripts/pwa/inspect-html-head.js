#!/usr/bin/env node

/**
 * HTML Head Inspector
 * This script fetches the actual HTML from your running Next.js server 
 * and shows EXACTLY what iOS Safari will see in the <head> tags
 * 
 * Usage:
 * 1. Start your dev server: npm run dev (or production build)
 * 2. Run: node scripts/inspect-html-head.js http://localhost:3000
 */

const http = require('http');
const https = require('https'); const url = process.argv[2] || 'http://localhost:3000';

const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  cyan: '\x1b[36m',
  bold: '\x1b[1m',
  magenta: '\x1b[35m',
};

function log(color, symbol, message) {
  console.log(`${color}${symbol}${colors.reset} ${message}`);
}

function fetchHTML(targetUrl) {
  return new Promise((resolve, reject) => {
    const parsedUrl = new URL(targetUrl);
    const protocol = parsedUrl.protocol === 'https:' ? https : http;

    const options = {
      hostname: parsedUrl.hostname,
      port: parsedUrl.port,
      path: parsedUrl.pathname,
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
      },
    };

    const req = protocol.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => (data += chunk));
      res.on('end', () => resolve(data));
    });

    req.on('error', reject);
    req.setTimeout(10000, () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });

    req.end();
  });
}

function extractHeadContent(html) {
  const headMatch = html.match(/<head[^>]*>([\s\S]*?)<\/head>/i);
  if (!headMatch) return null;
  return headMatch[1];
}

function extractIconTags(headContent) {
  const iconRegex = /<link[^>]*(?:rel=["'](?:icon|apple-touch-icon|apple-touch-icon-precomposed|shortcut icon|shortcut)["'])[^>]*>/gi;
  return headContent.match(iconRegex) || [];
}

function extractMetaTags(headContent) {
  const metaRegex = /<meta[^>]*(?:name=["'](?:theme-color|apple-mobile-web-app|application-name)["']|property=["']og:image["'])[^>]*>/gi;
  return headContent.match(metaRegex) || [];
}

function extractManifestLink(headContent) {
  const manifestRegex = /<link[^>]*rel=["']manifest["'][^>]*>/gi;
  return headContent.match(manifestRegex) || [];
}

function parseTag(tag) {
  const result = {};
  
  // Extract rel
  const relMatch = tag.match(/rel=["']([^"']+)["']/);
  if (relMatch) result.rel = relMatch[1];
  
  // Extract href
  const hrefMatch = tag.match(/href=["']([^"']+)["']/);
  if (hrefMatch) result.href = hrefMatch[1];
  
  // Extract sizes
  const sizesMatch = tag.match(/sizes=["']([^"']+)["']/);
  if (sizesMatch) result.sizes = sizesMatch[1];
  
  // Extract type
  const typeMatch = tag.match(/type=["']([^"']+)["']/);
  if (typeMatch) result.type = typeMatch[1];

  // Extract content (for meta tags)
  const contentMatch = tag.match(/content=["']([^"']+)["']/);
  if (contentMatch) result.content = contentMatch[1];

  // Extract name (for meta tags)
  const nameMatch = tag.match(/name=["']([^"']+)["']/);
  if (nameMatch) result.name = nameMatch[1];

  return result;
}

async function main() {
  console.log(`\n${colors.cyan}${colors.bold}═══════════════════════════════════════════${colors.reset}`);
  console.log(`${colors.cyan}${colors.bold}  iOS PWA HTML Head Inspector${colors.reset}`);
  console.log(`${colors.cyan}${colors.bold}═══════════════════════════════════════════${colors.reset}\n`);

  log(colors.cyan, '→', `Fetching HTML from: ${url}`);
  log(colors.cyan, 'ℹ', 'Simulating iPhone Safari User-Agent');
  console.log('');

  try {
    const html = await fetchHTML(url);
    const headContent = extractHeadContent(html);

    if (!headContent) {
      log(colors.red, '✗', 'Could not extract <head> content from HTML');
      process.exit(1);
    }

    const iconTags = extractIconTags(headContent);
    const metaTags = extractMetaTags(headContent);
    const manifestTags = extractManifestLink(headContent);

    // Display Icon Tags
    console.log(`${colors.bold}📱 Icon Tags (What iOS Will Use):${colors.reset}\n`);
    
    if (iconTags.length === 0) {
      log(colors.red, '✗', 'NO ICON TAGS FOUND! iOS will generate a screenshot');
    } else {
      iconTags.forEach((tag, idx) => {
        const parsed = parseTag(tag);
        console.log(`${colors.green}[${idx + 1}]${colors.reset} ${colors.bold}${parsed.rel || 'icon'}${colors.reset}`);
        console.log(`    ${colors.cyan}href:${colors.reset}  ${parsed.href || 'NOT SET'}`);
        if (parsed.sizes) console.log(`    ${colors.cyan}sizes:${colors.reset} ${parsed.sizes}`);
        if (parsed.type) console.log(`    ${colors.cyan}type:${colors.reset}  ${parsed.type}`);
        console.log('');
      });
    }

    // iOS Priority Explanation
    console.log(`${colors.yellow}${colors.bold}iOS Icon Selection Priority:${colors.reset}`);
    console.log(`  1. ${colors.green}apple-touch-icon${colors.reset} (180x180 preferred)`);
    console.log(`  2. ${colors.green}apple-touch-icon-precomposed${colors.reset}`);
    console.log(`  3. Manifest icons (if manifest linked)`);
    console.log(`  4. Generic <link rel="icon"> tags`);
    console.log(`  5. ${colors.red}Screenshot fallback${colors.reset} (if none found)\n`);

    // Find the primary iOS icon
    const appleIcon = iconTags.find(tag => tag.includes('apple-touch-icon') && !tag.includes('precomposed'));
    const applePrecomposed = iconTags.find(tag => tag.includes('apple-touch-icon-precomposed'));
    
    let primaryIcon = null;
    if (appleIcon) {
      primaryIcon = parseTag(appleIcon);
      log(colors.green, '✓', `PRIMARY iOS Icon: ${primaryIcon.href}`);
    } else if (applePrecomposed) {
      primaryIcon = parseTag(applePrecomposed);
      log(colors.green, '✓', `PRIMARY iOS Icon: ${primaryIcon.href}`);
    } else {
      log(colors.red, '✗', 'NO apple-touch-icon found!');
      log(colors.yellow, '⚠', 'iOS will use a screenshot or generic icon');
    }
    console.log('');

    // Display Manifest
    console.log(`${colors.bold}📄 Web App Manifest:${colors.reset}\n`);
    if (manifestTags.length > 0) {
      manifestTags.forEach(tag => {
        const parsed = parseTag(tag);
        log(colors.green, '✓', `Manifest linked: ${parsed.href}`);
      });
    } else {
      log(colors.red, '✗', 'No manifest.json link found');
    }
    console.log('');

    // Display Meta Tags
    console.log(`${colors.bold}🎨 Theme & Meta Tags:${colors.reset}\n`);
    if (metaTags.length > 0) {
      metaTags.forEach(tag => {
        const parsed = parseTag(tag);
        console.log(`  ${colors.cyan}${parsed.name || 'meta'}:${colors.reset} ${parsed.content}`);
      });
    } else {
      log(colors.yellow, 'ℹ', 'No relevant meta tags found');
    }
    console.log('');

    // Final Verdict
    console.log(`${colors.cyan}${colors.bold}═══════════════════════════════════════════${colors.reset}`);
    console.log(`${colors.bold}VERDICT${colors.reset}`);
    console.log(`${colors.cyan}${colors.bold}═══════════════════════════════════════════${colors.reset}\n`);

    if (appleIcon || applePrecomposed) {
      log(colors.green, '✓', 'iOS "Add to Home Screen" WILL use your custom icon');
      log(colors.green, '✓', `Icon path: ${primaryIcon.href}`);
      console.log(`\n${colors.green}${colors.bold}🎉 Configuration is correct!${colors.reset}`);
      console.log(`\n${colors.magenta}To test on iPhone:${colors.reset}`);
      console.log(`  1. Open Safari and navigate to your app`);
      console.log(`  2. Tap the Share button`);
      console.log(`  3. Tap "Add to Home Screen"`);
      console.log(`  4. You should see your custom icon preview\n`);
    } else {
      log(colors.red, '✗', 'iOS will NOT use a custom icon');
      log(colors.yellow, '⚠', 'It will create a screenshot instead');
      console.log(`\n${colors.red}${colors.bold}⚠ Configuration needs fixing${colors.reset}`);
      console.log(`\n${colors.yellow}Fix:${colors.reset}`);
      console.log(`  Add this to app/layout.tsx metadata.icons:`);
      console.log(`  ${colors.cyan}apple: [{ url: '/apple-touch-icon.png', sizes: '180x180' }]${colors.reset}\n`);
    }

  } catch (error) {
    log(colors.red, '✗', `Error: ${error.message}`);
    console.log(`\n${colors.yellow}Make sure your Next.js server is running:${colors.reset}`);
    console.log(`  npm run dev\n`);
    process.exit(1);
  }
}

main();
