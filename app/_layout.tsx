import 'react-native-get-random-values'
import { Buffer } from 'buffer'
if (typeof global.Buffer === 'undefined') {
  global.Buffer = Buffer
}
import '../tamagui-web.css'

import { useEffect } from 'react'
import { useColorScheme } from 'react-native'
import { StatusBar } from 'expo-status-bar'
import { DarkTheme, DefaultTheme, ThemeProvider } from '@react-navigation/native'
import { useFonts } from 'expo-font'
import { SplashScreen, Stack } from 'expo-router'
import { Provider } from 'components/Provider'
import { GlobalOverlayProvider } from 'components/GlobalOverlayProvider'
import { GlobalAgentShell } from 'components/GlobalAgentShell'
import { useTheme } from 'tamagui'
import { useSetAtom } from 'jotai'
import { initHrmConfigAtom } from '../lib/state/hrm-atoms'
import { initModulePreferencesAtom } from '../lib/state/module-preferences-atoms'
import { initDashboardAtom } from '../lib/state/dashboard-atoms'

export {
  // Catch any errors thrown by the Layout component.
  ErrorBoundary,
} from 'expo-router'

export const unstable_settings = {
  // Ensure that reloading on `/modal` keeps a back button present.
  initialRouteName: '(tabs)',
}

// Prevent the splash screen from auto-hiding before asset loading is complete.
SplashScreen.preventAutoHideAsync()

export default function RootLayout() {
  const [interLoaded, interError] = useFonts({
    Inter: require('@tamagui/font-inter/otf/Inter-Medium.otf'),
    InterBold: require('@tamagui/font-inter/otf/Inter-Bold.otf'),
  })

  useEffect(() => {
    if (interLoaded || interError) {
      // Hide the splash screen after the fonts have loaded (or an error was returned) and the UI is ready.
      SplashScreen.hideAsync()
    }
  }, [interLoaded, interError])

  if (!interLoaded && !interError) {
    return null
  }

  return (
    <Providers>
      <StateInitializer>
        <RootLayoutNav />
      </StateInitializer>
    </Providers>
  )
}

const Providers = ({ children }: { children: React.ReactNode }) => {
  return (
    <Provider>
      <GlobalOverlayProvider>
        {children}
        <GlobalAgentShell />
      </GlobalOverlayProvider>
    </Provider>
  )
}

// Initialize persisted state from AsyncStorage
function StateInitializer({ children }: { children: React.ReactNode }) {
  const initHrmConfig = useSetAtom(initHrmConfigAtom);
  const initModulePreferences = useSetAtom(initModulePreferencesAtom);
  const initDashboard = useSetAtom(initDashboardAtom);
  
  useEffect(() => {
    // Load persisted configurations from storage on app start
    initHrmConfig();
    initModulePreferences();
    initDashboard();
  }, [initHrmConfig, initModulePreferences, initDashboard]);
  
  return <>{children}</>;
}

function RootLayoutNav() {
  const colorScheme = useColorScheme()
  const theme = useTheme()
  
  // Force dark theme for the void aesthetic
  const voidTheme = {
    ...DarkTheme,
    colors: {
      ...DarkTheme.colors,
      background: '#050505',
      card: '#050505',
      text: '#FFFFFF',
      border: '#1A1A1A',
      notification: '#00FFFF',
    },
  };
  
  return (
    <ThemeProvider value={voidTheme}>
      <StatusBar style="light" />
      <Stack
        screenOptions={{
          headerShown: false,
          contentStyle: {
            backgroundColor: '#050505',
          },
          animation: 'fade',
        }}
      >
        <Stack.Screen
          name="(tabs)"
          options={{
            headerShown: false,
          }}
        />
        
        <Stack.Screen
          name="genesis"
          options={{
            headerShown: false,
            contentStyle: {
              backgroundColor: '#050505',
            },
          }}
        />
        
        <Stack.Screen
          name="settings"
          options={{
            headerShown: false,
            contentStyle: {
              backgroundColor: '#050505',
            },
          }}
        />

        <Stack.Screen
          name="modal"
          options={{
            title: 'Tamagui + Expo',
            presentation: 'modal',
            animation: 'slide_from_right',
            gestureEnabled: true,
            gestureDirection: 'horizontal',
            headerShown: true,
            headerStyle: {
              backgroundColor: '#050505',
            },
            headerTintColor: '#FFFFFF',
            contentStyle: {
              backgroundColor: '#050505',
            },
          }}
        />
      </Stack>
    </ThemeProvider>
  )
}
