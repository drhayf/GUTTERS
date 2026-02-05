#!/usr/bin/env node

/**
 * PWA Icon Generator
 * Generates all PWA icons from a source image
 * 
 * Usage:
 * 1. Place source-icon.png (at least 1024x1024) in the project root
 * 2. Run: pnpm install sharp (if not already installed)
 * 3. Run: node scripts/generate-pwa-icons.js
 */

const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

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

// Icon specs for PWA
const iconSpecs = [
  { name: 'apple-touch-icon.png', size: 180, output: 'public/apple-touch-icon.png' },
  { name: 'apple-touch-icon-precomposed.png', size: 180, output: 'public/apple-touch-icon-precomposed.png' },
  { name: 'apple-icon.png', size: 192, output: 'public/icons/apple-icon.png' },
  { name: 'icon-192.png', size: 192, output: 'public/icons/icon-192.png' },
  { name: 'icon-512.png', size: 512, output: 'public/icons/icon-512.png' },
];

async function generateIcons(sourcePath) {
  console.log(`\n${colors.cyan}${colors.bold}═══════════════════════════════════════════${colors.reset}`);
  console.log(`${colors.cyan}${colors.bold}  PWA Icon Generator${colors.reset}`);
  console.log(`${colors.cyan}${colors.bold}═══════════════════════════════════════════${colors.reset}\n`);

  // Verify source file exists
  if (!fs.existsSync(sourcePath)) {
    log(colors.red, '✗', `Source file not found: ${sourcePath}`);
    console.log(`\n${colors.yellow}Please provide a source icon:${colors.reset}`);
    console.log(`  1. Create a high-resolution icon (1024x1024 PNG/JPG)`);
    console.log(`  2. Save it as: ${sourcePath}`);
    console.log(`  3. Run this script again\n`);
    process.exit(1);
  }

  log(colors.cyan, '→', `Source: ${sourcePath}`);

  // Validate source image with sharp
  console.log(`\n${colors.bold}Validating source image...${colors.reset}`);

  try {
    const sourceInfo = await sharp(sourcePath).metadata();

    // Check format
    const supportedFormats = ['jpeg', 'jpg', 'png', 'webp', 'tiff', 'svg'];
    if (!supportedFormats.includes(sourceInfo.format.toLowerCase())) {
      log(colors.red, '✗', `Unsupported format: ${sourceInfo.format}`);
      log(colors.yellow, 'ℹ', 'Supported: JPG, PNG, WebP, TIFF');
      process.exit(1);
    }
    log(colors.green, '✓', `Format: ${sourceInfo.format.toUpperCase()}`);

    // Check dimensions
    log(colors.green, '✓', `Dimensions: ${sourceInfo.width}x${sourceInfo.height}`);

    if (sourceInfo.width < 512 || sourceInfo.height < 512) {
      log(colors.red, '✗', 'Image too small! Minimum 512x512 recommended');
      log(colors.yellow, 'ℹ', '1024x1024 is ideal for best quality');
      process.exit(1);
    }

    if (sourceInfo.width !== sourceInfo.height) {
      log(colors.yellow, '⚠', 'Image is not square - will be fitted with transparent padding');
    }

    // Check color space
    log(colors.green, '✓', `Color space: ${sourceInfo.space || 'RGB'}`);

    // Check for transparency
    if (sourceInfo.hasAlpha) {
      log(colors.green, '✓', 'Has transparency (alpha channel)');
    } else {
      log(colors.cyan, 'ℹ', 'No transparency - will add if needed');
    }

    // File size
    const stats = fs.statSync(sourcePath);
    const sizeMB = (stats.size / 1024 / 1024).toFixed(2);
    log(colors.green, '✓', `File size: ${sizeMB} MB`);

    log(colors.green, '\n✓', 'Source image is valid!');

  } catch (error) {
    log(colors.red, '✗', `Failed to read image: ${error.message}`);
    log(colors.yellow, 'ℹ', 'Make sure the file is a valid image');
    process.exit(1);
  }

  console.log('');

  // Create icons directory if it doesn't exist
  if (!fs.existsSync('public/icons')) {
    fs.mkdirSync('public/icons', { recursive: true });
    log(colors.green, '✓', 'Created public/icons directory');
  }

  // Generate each icon
  for (const spec of iconSpecs) {
    try {
      // Generate PNG buffer first with proper color mode for iOS
      const buffer = await sharp(sourcePath)
        .resize(spec.size, spec.size, {
          fit: 'contain',
          background: { r: 0, g: 0, b: 0, alpha: 0 }
        })
        .ensureAlpha() // Force RGBA color mode (iOS compatible)
        .png({
          compressionLevel: 9,
          quality: 100,
          force: true,
          palette: false // Disable indexed/palette mode
        })
        .toBuffer();

      // Write buffer to file (ensures proper IEND chunk)
      fs.writeFileSync(spec.output, buffer);

      const stats = fs.statSync(spec.output);
      const sizeKB = (stats.size / 1024).toFixed(2);
      log(colors.green, '✓', `${spec.name} (${spec.size}x${spec.size}, ${sizeKB} KB)`);
    } catch (error) {
      log(colors.red, '✗', `Failed to generate ${spec.name}: ${error.message}`);
    }
  }

  console.log('');
  console.log(`${colors.green}${colors.bold}🎉 All icons generated successfully!${colors.reset}`);
  console.log(`\n${colors.cyan}Next steps:${colors.reset}`);
  console.log(`  1. Run: ${colors.yellow}node scripts/check-pwa-icons.js${colors.reset}`);
  console.log(`  2. Verify all icons are valid\n`);
}

// Find source file
const possibleSources = [
  'source-icon.jpg',
  'source-icon.jpeg',
  'source-icon.png',
  'icon-source.jpg',
  'icon-source.png',
  'logo.jpg',
  'logo.jpeg',
  'logo.png',
  'app-icon.jpg',
  'app-icon.png',
];

let sourcePath = process.argv[2];

if (!sourcePath) {
  // Try to find a source file
  for (const src of possibleSources) {
    if (fs.existsSync(src)) {
      sourcePath = src;
      break;
    }
  }
}

if (!sourcePath) {
  console.log(`\n${colors.red}${colors.bold}No source icon found!${colors.reset}\n`);
  console.log(`${colors.yellow}Usage:${colors.reset}`);
  console.log(`  node scripts/generate-pwa-icons.js <source-image.png>\n`);
  console.log(`${colors.yellow}Or place one of these files in the project root:${colors.reset}`);
  possibleSources.forEach(src => console.log(`  - ${src}`));
  console.log('');
  process.exit(1);
}

generateIcons(sourcePath).catch(error => {
  log(colors.red, '✗', `Error: ${error.message}`);
  process.exit(1);
});
