#!/usr/bin/env node

/**
 * PWA Icon Verification Script
 * Run this to verify all PWA icons are configured correctly
 * Usage: node scripts/check-pwa-icons.js
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// ANSI color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  cyan: '\x1b[36m',
  bold: '\x1b[1m',
};

function log(color, symbol, message) {
  console.log(`${color}${symbol}${colors.reset} ${message}`);
}

function readUInt32BE(buffer, offset) {
  return (buffer[offset] << 24) | (buffer[offset + 1] << 16) | (buffer[offset + 2] << 8) | buffer[offset + 3];
}

function deepValidatePNG(buffer) {
  const errors = [];
  const warnings = [];
  const info = {};

  // PNG Magic Number: 89 50 4E 47 0D 0A 1A 0A
  const pngSignature = [0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A];
  for (let i = 0; i < 8; i++) {
    if (buffer[i] !== pngSignature[i]) {
      errors.push('Invalid PNG signature - file is corrupted');
      return { valid: false, errors, warnings, info };
    }
  }

  // Read IHDR chunk (Image Header)
  let offset = 8;
  const ihdrLength = readUInt32BE(buffer, offset);
  offset += 4;

  const ihdrType = buffer.toString('ascii', offset, offset + 4);
  if (ihdrType !== 'IHDR') {
    errors.push('IHDR chunk not found - PNG structure invalid');
    return { valid: false, errors, warnings, info };
  }
  offset += 4;

  // Parse IHDR data
  info.width = readUInt32BE(buffer, offset);
  info.height = readUInt32BE(buffer, offset + 4);
  info.bitDepth = buffer[offset + 8];
  info.colorType = buffer[offset + 9];
  info.compression = buffer[offset + 10];
  info.filter = buffer[offset + 11];
  info.interlace = buffer[offset + 12];

  // Validate dimensions
  if (info.width === 0 || info.height === 0) {
    errors.push('Invalid dimensions (0x0)');
  }
  if (info.width > 2048 || info.height > 2048) {
    warnings.push(`Large dimensions (${info.width}x${info.height}) - iOS prefers 180x180 to 1024x1024`);
  }

  // Validate color type (iOS compatibility)
  const colorTypes = {
    0: 'Grayscale',
    2: 'RGB',
    3: 'Indexed',
    4: 'Grayscale + Alpha',
    6: 'RGBA'
  };
  info.colorTypeName = colorTypes[info.colorType] || 'Unknown';

  if (info.colorType === 3) {
    warnings.push('Indexed color mode - iOS prefers RGB or RGBA');
  }

  // Validate bit depth
  if (info.bitDepth !== 8 && info.colorType !== 3) {
    warnings.push(`Bit depth ${info.bitDepth} - iOS prefers 8-bit per channel`);
  }

  // Validate compression
  if (info.compression !== 0) {
    errors.push('Invalid compression method - must be 0 (deflate)');
  }

  // Check for critical chunks
  let hasIDAT = false;
  let hasIEND = false;
  offset = 8; // Reset to start of chunks

  try {
    while (offset < buffer.length - 12) {
      const chunkLength = readUInt32BE(buffer, offset);
      const chunkType = buffer.toString('ascii', offset + 4, offset + 8);
      
      if (chunkType === 'IDAT') hasIDAT = true;
      if (chunkType === 'IEND') {
        hasIEND = true;
        break; // IEND is always last
      }

      // Jump to next chunk
      offset += 12 + chunkLength; // Length (4) + Type (4) + Data (chunkLength) + CRC (4)
      
      // Safety check to prevent infinite loops
      if (offset >= buffer.length) break;
    }
  } catch (error) {
    errors.push('Failed to parse PNG chunks - file may be corrupted');
  }

  if (!hasIDAT) errors.push('Missing IDAT chunk - image data corrupted');
  if (!hasIEND) {
    // Double check at end of file for IEND
    const last8Bytes = buffer.slice(-12);
    const endMarker = last8Bytes.toString('ascii', 4, 8);
    if (endMarker === 'IEND') {
      hasIEND = true;
    } else {
      errors.push('Missing IEND chunk - file truncated');
    }
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings,
    info
  };
}

function checkIcon(iconPath) {
  const fullPath = path.join(process.cwd(), iconPath);
  
  try {
    const stats = fs.statSync(fullPath);
    const buffer = fs.readFileSync(fullPath);
    const hash = crypto.createHash('md5').update(buffer).digest('hex').substring(0, 8);
    const sizeKB = (stats.size / 1024).toFixed(2);

    if (iconPath.endsWith('.png')) {
      // Deep PNG validation
      const validation = deepValidatePNG(buffer);
      
      if (!validation.valid) {
        log(colors.red, '✗', `${iconPath.replace('public/', '/')} - CORRUPTED`);
        validation.errors.forEach(err => {
          console.log(`      ${colors.red}└─ ${err}${colors.reset}`);
        });
        return { exists: true, valid: false, error: validation.errors.join(', ') };
      }

      // Display PNG info
      log(colors.green, '✓', `${iconPath.replace('public/', '/')} (${sizeKB} KB, hash: ${hash})`);
      console.log(`      ${colors.cyan}└─ ${validation.info.width}x${validation.info.height}, ${validation.info.bitDepth}-bit ${validation.info.colorTypeName}${colors.reset}`);
      
      // Show warnings
      if (validation.warnings.length > 0) {
        validation.warnings.forEach(warn => {
          console.log(`      ${colors.yellow}⚠  ${warn}${colors.reset}`);
        });
      }

      return { exists: true, valid: true, size: stats.size, hash, info: validation.info };

    } else if (iconPath.endsWith('.ico')) {
      const isICO = buffer[0] === 0x00 && buffer[1] === 0x00 && buffer[2] === 0x01 && buffer[3] === 0x00;
      if (!isICO) {
        log(colors.red, '✗', `${iconPath.replace('public/', '/')} - Not a valid ICO file`);
        return { exists: true, valid: false, error: 'Not a valid ICO file' };
      }
      log(colors.green, '✓', `${iconPath.replace('public/', '/')} (${sizeKB} KB, hash: ${hash})`);
      return { exists: true, valid: true, size: stats.size, hash };
    }

  } catch (error) {
    if (error.code === 'ENOENT') {
      log(colors.red, '✗', `${iconPath.replace('public/', '/')} - File not found`);
      return { exists: false, valid: false, error: 'File not found' };
    }
    log(colors.red, '✗', `${iconPath.replace('public/', '/')} - ${error.message}`);
    return { exists: false, valid: false, error: error.message };
  }
}

function checkConflicts() {
  const conflictPaths = [
    'app/icon.png',
    'app/icon.tsx',
    'app/icon.ts',
    'app/apple-icon.png',
    'app/apple-icon.tsx',
    'app/apple-icon.ts',
    'app/favicon.ico',
  ];

  const conflicts = [];

  for (const conflictPath of conflictPaths) {
    const fullPath = path.join(process.cwd(), conflictPath);
    if (fs.existsSync(fullPath)) {
      conflicts.push(conflictPath);
      log(colors.red, '⚠', `CONFLICT: ${conflictPath} exists and will OVERRIDE public/ icons`);
    }
  }

  return conflicts;
}

function checkManifest() {
  const manifestPath = path.join(process.cwd(), 'public/manifest.json');
  
  try {
    const manifestContent = fs.readFileSync(manifestPath, 'utf-8');
    const manifest = JSON.parse(manifestContent);
    
    log(colors.green, '✓', 'manifest.json is valid');
    
    console.log(`\n${colors.cyan}${colors.bold}Manifest Content:${colors.reset}`);
    console.log(`  Name: ${manifest.name}`);
    console.log(`  Short Name: ${manifest.short_name}`);
    console.log(`  Theme Color: ${manifest.theme_color}`);
    console.log(`  Background Color: ${manifest.background_color}`);
    console.log(`  Icons: ${manifest.icons?.length || 0}`);
    
    return { valid: true, manifest };
  } catch (error) {
    log(colors.red, '✗', `manifest.json error: ${error.message}`);
    return { valid: false, error: error.message };
  }
}

// Main execution
console.log(`\n${colors.cyan}${colors.bold}═══════════════════════════════════════════${colors.reset}`);
console.log(`${colors.cyan}${colors.bold}  PWA Icon Verification Script${colors.reset}`);
console.log(`${colors.cyan}${colors.bold}═══════════════════════════════════════════${colors.reset}\n`);

// Check for conflicts first (most critical)
console.log(`${colors.bold}1. Checking for conflicting app/ directory icons...${colors.reset}`);
const conflicts = checkConflicts();
if (conflicts.length === 0) {
  log(colors.green, '✓', 'No conflicting app/ directory icons found - GOOD!');
}
console.log('');

// Check required icons
console.log(`${colors.bold}2. Checking required icon files...${colors.reset}`);
const requiredIcons = [
  'public/apple-touch-icon.png',
  'public/apple-touch-icon-precomposed.png',
  'public/icons/apple-icon.png',
  'public/icons/icon-192.png',
  'public/icons/icon-512.png',
];

// Optional icons (browser tabs only, not needed for iOS PWA)
const optionalIcons = ['public/favicon.ico'];

const iconResults = requiredIcons.map(checkIcon);
const validIcons = iconResults.filter(r => r.exists && r.valid).length;
const totalIcons = requiredIcons.length;

// Check optional icons
console.log(`\n${colors.bold}Optional (browser-only icons):${colors.reset}`);
optionalIcons.forEach(icon => {
  const result = checkIcon(icon);
  if (!result.exists || !result.valid) {
    log(colors.yellow, 'ℹ', `${icon.replace('public/', '/')} is optional for iOS PWA`);
  }
});
console.log('');

// Check manifest
console.log(`${colors.bold}3. Checking manifest.json...${colors.reset}`);
const manifestResult = checkManifest();
console.log('');

// Summary
console.log(`${colors.cyan}${colors.bold}═══════════════════════════════════════════${colors.reset}`);
console.log(`${colors.bold}SUMMARY${colors.reset}`);
console.log(`${colors.cyan}${colors.bold}═══════════════════════════════════════════${colors.reset}\n`);

const allGood = conflicts.length === 0 && validIcons === totalIcons && manifestResult.valid;

if (allGood) {
  log(colors.green, '✓', `All PWA icons are configured correctly! (${validIcons}/${totalIcons})`);
  log(colors.green, '✓', 'No conflicts detected');
  log(colors.green, '✓', 'Manifest is valid');
  console.log(`\n${colors.green}${colors.bold}🎉 PWA configuration is ready for iOS "Add to Home Screen"!${colors.reset}\n`);
  process.exit(0);
} else {
  if (conflicts.length > 0) {
    log(colors.red, '✗', `${conflicts.length} conflicting file(s) in app/ directory`);
    console.log(`\n${colors.yellow}Action Required: Delete these files:${colors.reset}`);
    conflicts.forEach(c => console.log(`  rm ${c}`));
  }
  
  const invalidCount = totalIcons - validIcons;
  if (invalidCount > 0) {
    log(colors.red, '✗', `${invalidCount} icon(s) missing or invalid`);
  }
  
  if (!manifestResult.valid) {
    log(colors.red, '✗', 'Manifest is invalid or missing');
  }
  
  console.log(`\n${colors.red}${colors.bold}⚠ PWA configuration needs attention${colors.reset}\n`);
  process.exit(1);
}
