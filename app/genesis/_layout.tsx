import { Stack } from 'expo-router';

export default function GenesisLayout() {
  return (
    <Stack
      screenOptions={{
        headerShown: false,
        animation: 'fade',
        contentStyle: {
          backgroundColor: '#050505',
        },
      }}
    />
  );
}
