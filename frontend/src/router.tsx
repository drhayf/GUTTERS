import { createBrowserRouter, Navigate } from 'react-router-dom'
import AppShell from './components/layout/AppShell'
import ChatInterface from './components/chat/ChatInterface'
import LoginPage from './features/auth/components/LoginPage'
import RegisterPage from './features/auth/components/RegisterPage'
import OnboardingCheck from './components/onboarding/OnboardingCheck'
import OnboardingFlow from './features/onboarding/OnboardingFlow'
import DashboardPage from './features/dashboard/DashboardPage'
import ControlRoomPage from './features/system/ControlRoomPage'
import JournalPage from './features/journal/JournalPage'
import ProfilePage from './features/profile/ProfilePage'
import { TrackingPage } from './features/tracking/TrackingPage'
import TimelinePage from './features/timeline/TimelinePage'
import CouncilPage from './features/council/CouncilPage'
import OraclePage from './features/oracle/OraclePage'

import NotificationSettingsPage from './features/settings/NotificationSettingsPage'

export const router = createBrowserRouter([
    {
        path: '/login',
        element: <LoginPage />
    },
    {
        path: '/register',
        element: <RegisterPage />
    },
    {
        path: '/onboarding',
        element: (
            <OnboardingCheck>
                <OnboardingFlow />
            </OnboardingCheck>
        )
    },
    {
        path: '/',
        element: <AppShell />,
        children: [
            {
                index: true,
                element: <Navigate to="/dashboard" replace />
            },
            {
                path: 'dashboard',
                element: <DashboardPage />
            },
            {
                path: 'chat',
                element: <ChatInterface />
            },
            {
                path: 'chat/:conversationId',
                element: <ChatInterface />
            },
            {
                path: 'control-room',
                element: <ControlRoomPage />
            },
            {
                path: 'journal',
                element: <JournalPage />
            },
            {
                path: 'profile',
                element: <ProfilePage />
            },
            {
                path: 'tracking',
                element: <TrackingPage />
            },
            {
                path: 'timeline',
                element: <TimelinePage />
            },
            {
                path: 'council',
                element: <CouncilPage />
            },
            {
                path: 'oracle',
                element: <OraclePage />
            },
            {
                path: 'settings/notifications',
                element: <NotificationSettingsPage />
            }
        ]
    }
])
