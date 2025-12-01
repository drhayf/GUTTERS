import React, { useEffect, useState } from 'react';
import { StyleSheet, View, Dimensions, Platform } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedProps,
  withRepeat,
  withTiming,
  withSequence,
  Easing,
} from 'react-native-reanimated';
import { useAtomValue } from 'jotai';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Svg, { Path } from 'react-native-svg';
import * as Device from 'expo-device';
import { aiStateAtom } from '../../lib/state/genesis-atoms';

const AnimatedPath = Animated.createAnimatedComponent(Path);
const AnimatedView = Animated.createAnimatedComponent(View);

// NOTE: Dimensions.get('window') returns LOGICAL pixels (points), not physical pixels
// The safe area insets are also in logical pixels
// For iPhone 12 Pro Max: 428 x 926 points (actual screen is 1284 x 2778 physical pixels @ 3x)
const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

// Device-specific notch/Dynamic Island configurations
// All measurements in LOGICAL PIXELS (points)
// 
// ┌─────────────────────────────────────────────────────────────────┐
// │  HOW TO ADJUST CORNER RADII:                                    │
// │                                                                 │
// │  screenCornerRadius = TOP corners (where time/battery are)      │
// │  bottomCornerRadius = BOTTOM corners (where home indicator is)  │
// │                                                                 │
// │  - INCREASE value = corners curve MORE (go further off-screen)  │
// │  - DECREASE value = corners curve LESS (stay more on-screen)    │
// │                                                                 │
// │  For iPhone 12 Pro Max, adjust the "Max/Plus models" section    │
// └─────────────────────────────────────────────────────────────────┘
type NotchConfig = {
  type: 'notch' | 'dynamic-island' | 'none';
  width: number;           // Width of the notch/island
  height: number;          // Height from top of screen
  cornerRadius: number;    // Radius of notch corners
  screenCornerRadius: number;  // TOP screen corner radius
  bottomCornerRadius: number;  // BOTTOM screen corner radius
};

// More comprehensive device detection using actual model identifiers
// See: https://gist.github.com/adamawolf/3048717
const getDeviceNotchConfig = (modelId: string | null, insetTop: number, screenWidth: number): NotchConfig => {
  // Default for devices with home button (no notch)
  if (insetTop < 30) {
    return { type: 'none', width: 0, height: 0, cornerRadius: 0, screenCornerRadius: 0, bottomCornerRadius: 0 };
  }

  // iPhone model identifiers:
  // iPhone X: iPhone10,3 / iPhone10,6
  // iPhone XS: iPhone11,2
  // iPhone XS Max: iPhone11,4 / iPhone11,6
  // iPhone XR: iPhone11,8
  // iPhone 11: iPhone12,1
  // iPhone 11 Pro: iPhone12,3
  // iPhone 11 Pro Max: iPhone12,5
  // iPhone 12 mini: iPhone13,1
  // iPhone 12: iPhone13,2
  // iPhone 12 Pro: iPhone13,3
  // iPhone 12 Pro Max: iPhone13,4
  // iPhone 13 mini: iPhone14,4
  // iPhone 13: iPhone14,5
  // iPhone 13 Pro: iPhone14,2
  // iPhone 13 Pro Max: iPhone14,3
  // iPhone 14: iPhone14,7
  // iPhone 14 Plus: iPhone14,8
  // iPhone 14 Pro: iPhone15,2
  // iPhone 14 Pro Max: iPhone15,3
  // iPhone 15: iPhone15,4 / iPhone15,5
  // iPhone 15 Pro: iPhone16,1
  // iPhone 15 Pro Max: iPhone16,2

  // Dynamic Island devices (iPhone 14 Pro and later - iPhone15,2+)
  const isDynamicIsland = modelId?.match(/iPhone1[5-9],/) || modelId?.match(/iPhone[2-9]\d,/);
  
  if (isDynamicIsland) {
    return {
      type: 'dynamic-island',
      width: 126,
      height: 37,
      cornerRadius: 18,
      screenCornerRadius: 52,    // TOP corners
      bottomCornerRadius: 52,    // BOTTOM corners
    };
  }

  // ╔═══════════════════════════════════════════════════════════════════╗
  // ║  iPhone 12 Pro Max (iPhone13,4) - ADJUST THESE VALUES             ║
  // ║  Screen width: 428pt                                              ║
  // ╠═══════════════════════════════════════════════════════════════════╣
  // ║  screenCornerRadius: TOP corners (was 53, now 50)                 ║
  // ║  bottomCornerRadius: BOTTOM corners (was 20, now 38)              ║
  // ║                                                                   ║
  // ║  ↑ INCREASE = more curve (goes off screen)                        ║
  // ║  ↓ DECREASE = less curve (stays on screen)                        ║
  // ╚═══════════════════════════════════════════════════════════════════╝
  if (screenWidth > 400) {
    return {
      type: 'notch',
      width: 215,
      height: 34,
      cornerRadius: 22,
      screenCornerRadius: 60,    // TOP corners - reduced from 53
      bottomCornerRadius: 70,    // BOTTOM corners - increased from 20 to bring them in
    };
  }

  // Standard/Pro models (~390pt width)
  if (screenWidth > 370) {
    return {
      type: 'notch',
      width: 209,
      height: 34,
      cornerRadius: 20,
      screenCornerRadius: 44,
      bottomCornerRadius: 35,
    };
  }

  // Mini models (~375pt width)
  return {
    type: 'notch',
    width: 195,
    height: 32,
    cornerRadius: 18,
    screenCornerRadius: 42,
    bottomCornerRadius: 32,
  };
};

// Generate SVG path for edge-to-edge border with notch cutout
const generateBorderPath = (
  width: number,
  height: number,
  notch: NotchConfig,
  insets: { top: number; bottom: number; left: number; right: number },
  borderInset: number = 2
): string => {
  const w = width - borderInset * 2;
  const h = height - borderInset * 2;
  const x = borderInset;
  const y = borderInset;
  const r = notch.screenCornerRadius || 20;      // TOP corner radius
  const br = notch.bottomCornerRadius || r;       // BOTTOM corner radius

  if (notch.type === 'none') {
    // Simple rounded rectangle for devices without notch
    return `
      M ${x + r} ${y}
      L ${x + w - r} ${y}
      Q ${x + w} ${y} ${x + w} ${y + r}
      L ${x + w} ${y + h - br}
      Q ${x + w} ${y + h} ${x + w - br} ${y + h}
      L ${x + br} ${y + h}
      Q ${x} ${y + h} ${x} ${y + h - br}
      L ${x} ${y + r}
      Q ${x} ${y} ${x + r} ${y}
      Z
    `;
  }

  // Calculate notch/island position
  const notchLeft = (width - notch.width) / 2;
  const notchRight = notchLeft + notch.width;
  const notchBottom = notch.height + y;
  const nr = notch.cornerRadius;

  if (notch.type === 'dynamic-island') {
    // Path that goes edge-to-edge but curves around Dynamic Island
    return `
      M ${x + r} ${y}
      L ${notchLeft - nr} ${y}
      Q ${notchLeft} ${y} ${notchLeft} ${y + nr}
      L ${notchLeft} ${notchBottom - nr}
      Q ${notchLeft} ${notchBottom} ${notchLeft + nr} ${notchBottom}
      L ${notchRight - nr} ${notchBottom}
      Q ${notchRight} ${notchBottom} ${notchRight} ${notchBottom - nr}
      L ${notchRight} ${y + nr}
      Q ${notchRight} ${y} ${notchRight + nr} ${y}
      L ${x + w - r} ${y}
      Q ${x + w} ${y} ${x + w} ${y + r}
      L ${x + w} ${y + h - br}
      Q ${x + w} ${y + h} ${x + w - br} ${y + h}
      L ${x + br} ${y + h}
      Q ${x} ${y + h} ${x} ${y + h - br}
      L ${x} ${y + r}
      Q ${x} ${y} ${x + r} ${y}
      Z
    `;
  }

  // Notch path (iPhone X - 14 style)
  return `
    M ${x + r} ${y}
    L ${notchLeft} ${y}
    L ${notchLeft} ${notchBottom - nr}
    Q ${notchLeft} ${notchBottom} ${notchLeft + nr} ${notchBottom}
    L ${notchRight - nr} ${notchBottom}
    Q ${notchRight} ${notchBottom} ${notchRight} ${notchBottom - nr}
    L ${notchRight} ${y}
    L ${x + w - r} ${y}
    Q ${x + w} ${y} ${x + w} ${y + r}
    L ${x + w} ${y + h - br}
    Q ${x + w} ${y + h} ${x + w - br} ${y + h}
    L ${x + br} ${y + h}
    Q ${x} ${y + h} ${x} ${y + h - br}
    L ${x} ${y + r}
    Q ${x} ${y} ${x + r} ${y}
    Z
  `;
};

interface PulsingBorderProps {
  children: React.ReactNode;
}

// Lunar beam color palette - ethereal, ambient glow like moonlight
// Multiple layers at very low opacity create a natural, diffuse illumination
const LUNAR_CORE = '#FFFFFF';       // Pure white at the very edge
const LUNAR_INNER = '#E8F4FF';      // Cool white
const LUNAR_MID = '#C8E0F8';        // Soft blue-white
const LUNAR_OUTER = '#A0C8E8';      // Diffuse blue glow

export function PulsingBorder({ children }: PulsingBorderProps) {
  const aiState = useAtomValue(aiStateAtom);
  const insets = useSafeAreaInsets();
  const [deviceModel, setDeviceModel] = useState<string | null>(null);
  
  // Organic breath animation - fades from completely invisible to subtle presence
  const breathIntensity = useSharedValue(0);
  
  useEffect(() => {
    if (Platform.OS === 'ios') {
      setDeviceModel(Device.modelId);
    }
  }, []);
  
  useEffect(() => {
    // Pulse timing based on AI state
    // Thinking = slightly faster, more present
    // Listening/Idle = slow, meditative breath
    const duration = aiState === 'thinking' ? 3000 : 5000;
    const maxIntensity = aiState === 'thinking' ? 1.0 : 0.7;
    
    // Organic breath cycle using sine easing for natural, wave-like motion
    // The animation should feel like the screen is gently breathing light
    breathIntensity.value = withRepeat(
      withSequence(
        // Inhale - light slowly gathers at the edges
        withTiming(maxIntensity, { 
          duration: duration * 0.45, 
          easing: Easing.inOut(Easing.sin)
        }),
        // Hold - brief moment of full presence
        withTiming(maxIntensity, { 
          duration: duration * 0.1, 
          easing: Easing.linear 
        }),
        // Exhale - light gently dissolves into darkness
        withTiming(0, { 
          duration: duration * 0.45, 
          easing: Easing.inOut(Easing.sin)
        })
      ),
      -1,
      false
    );
  }, [aiState]);

  const notchConfig = getDeviceNotchConfig(deviceModel, insets.top, SCREEN_WIDTH);
  const borderPath = generateBorderPath(SCREEN_WIDTH, SCREEN_HEIGHT, notchConfig, insets);

  // Outermost diffuse glow - very wide, very soft
  const outerGlowProps = useAnimatedProps(() => ({
    strokeOpacity: breathIntensity.value * 0.08,
    strokeWidth: 25,
  }));
  
  // Mid glow layer - medium width, soft
  const midGlowProps = useAnimatedProps(() => ({
    strokeOpacity: breathIntensity.value * 0.12,
    strokeWidth: 12,
  }));
  
  // Inner glow layer - narrower, slightly more visible
  const innerGlowProps = useAnimatedProps(() => ({
    strokeOpacity: breathIntensity.value * 0.18,
    strokeWidth: 5,
  }));
  
  // Core luminance - very thin, brightest point
  const coreGlowProps = useAnimatedProps(() => ({
    strokeOpacity: breathIntensity.value * 0.25,
    strokeWidth: 1.5,
  }));

  return (
    <View style={styles.container}>
      {/* Outermost diffuse glow - creates ambient atmosphere */}
      <View style={styles.glowLayer} pointerEvents="none">
        <Svg width={SCREEN_WIDTH} height={SCREEN_HEIGHT} style={StyleSheet.absoluteFill}>
          <AnimatedPath
            d={borderPath}
            stroke={LUNAR_OUTER}
            fill="none"
            animatedProps={outerGlowProps}
          />
        </Svg>
      </View>
      
      {/* Mid glow layer - builds up the luminance */}
      <View style={styles.glowLayer} pointerEvents="none">
        <Svg width={SCREEN_WIDTH} height={SCREEN_HEIGHT} style={StyleSheet.absoluteFill}>
          <AnimatedPath
            d={borderPath}
            stroke={LUNAR_MID}
            fill="none"
            animatedProps={midGlowProps}
          />
        </Svg>
      </View>
      
      {/* Inner glow - closer to the edge */}
      <View style={styles.glowLayer} pointerEvents="none">
        <Svg width={SCREEN_WIDTH} height={SCREEN_HEIGHT} style={StyleSheet.absoluteFill}>
          <AnimatedPath
            d={borderPath}
            stroke={LUNAR_INNER}
            fill="none"
            animatedProps={innerGlowProps}
          />
        </Svg>
      </View>
      
      {/* Core luminance - the brightest point at the very edge */}
      <View style={styles.glowLayer} pointerEvents="none">
        <Svg width={SCREEN_WIDTH} height={SCREEN_HEIGHT} style={StyleSheet.absoluteFill}>
          <AnimatedPath
            d={borderPath}
            stroke={LUNAR_CORE}
            fill="none"
            animatedProps={coreGlowProps}
          />
        </Svg>
      </View>
      
      {/* Content */}
      <View style={styles.content}>
        {children}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#050505',
  },
  glowLayer: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 9,
  },
  content: {
    flex: 1,
    zIndex: 1,
  },
});
