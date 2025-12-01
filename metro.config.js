// Learn more https://docs.expo.io/guides/customizing-metro
/**
 * @type {import('expo/metro-config').MetroConfig}
 */
const { getDefaultConfig } = require('expo/metro-config')
const { withTamagui } = require('@tamagui/metro-plugin')
const exclusionList = require('metro-config/src/defaults/exclusionList')

const config = getDefaultConfig(__dirname, {
  isCSSEnabled: true,
})

config.resolver.sourceExts.push('mjs')

config.resolver.extraNodeModules = {
  crypto: require.resolve('crypto-browserify'),
  stream: require.resolve('readable-stream'),
  buffer: require.resolve('buffer'),
}

config.resolver.blockList = exclusionList([
  /\.git\/.*/,
  /android\/.*/,
  /ios\/.*/,
  /attached_assets\/.*/,
  /apps\/api\/\.venv\/.*/,
  /apps\/api\/__pycache__\/.*/,
  /__pycache__\/.*/,
  /\.cache\/.*/,
])

config.watcher = {
  ...config.watcher,
  healthCheck: {
    enabled: false,
  },
  watchman: {
    deferStates: ['hg.update'],
  },
}

module.exports = withTamagui(config, {
  components: ['tamagui'],
  config: './tamagui.config.ts',
  outputCSS: './tamagui-web.css',
})
