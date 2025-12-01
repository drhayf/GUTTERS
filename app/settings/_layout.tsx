/**
 * Settings Layout
 */
import { Stack } from 'expo-router';
import { useTheme } from 'tamagui';

export default function SettingsLayout() {
  const theme = useTheme();
  
  return (
    <Stack
      screenOptions={{
        headerStyle: {
          backgroundColor: theme.background.val,
        },
        headerTintColor: theme.color.val,
        headerTitleStyle: {
          fontWeight: '600',
        },
        contentStyle: {
          backgroundColor: theme.background.val,
        },
      }}
    >
      <Stack.Screen
        name="index"
        options={{
          title: 'Settings',
        }}
      />
      <Stack.Screen
        name="hrm"
        options={{
          title: 'Reasoning Engine',
          presentation: 'modal',
        }}
      />
    </Stack>
  );
}
