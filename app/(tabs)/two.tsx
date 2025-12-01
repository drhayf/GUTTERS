import { StyleSheet, Platform, View } from 'react-native';
import { Text } from 'tamagui';
import Animated, { FadeIn } from 'react-native-reanimated';

export default function InsightsScreen() {
  return (
    <View style={styles.container}>
      <Animated.View entering={FadeIn.duration(800)} style={styles.content}>
        <Text style={styles.title}>DIGITAL TWIN</Text>
        <Text style={styles.subtitle}>Insights & Patterns</Text>
        <Text style={styles.description}>
          Complete the Genesis profiling to unlock your Digital Twin insights.
        </Text>
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#050505',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
  },
  content: {
    alignItems: 'center',
    gap: 16,
  },
  title: {
    color: 'rgba(255, 255, 255, 0.9)',
    fontSize: 24,
    fontWeight: '200',
    letterSpacing: 6,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  subtitle: {
    color: 'rgba(147, 51, 234, 0.7)',
    fontSize: 14,
    fontWeight: '500',
    letterSpacing: 2,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  description: {
    color: 'rgba(255, 255, 255, 0.4)',
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 22,
    marginTop: 24,
    paddingHorizontal: 32,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
});
