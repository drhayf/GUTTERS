import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { useAuthStore } from '../stores/authStore';

// Define the shape of our event packet
export interface EventPacket {
    source: string;
    event_type: string;
    payload: any;
    user_id?: string;
    timestamp: string;
}

interface GlobalEventsContextType {
    isConnected: boolean;
    lastEvent: EventPacket | null;
    events: EventPacket[]; // Keep a small buffer for debug/history
}

const GlobalEventsContext = createContext<GlobalEventsContextType | undefined>(undefined);

export const GlobalEventsProvider = ({ children }: { children: ReactNode }) => {
    const [isConnected, setIsConnected] = useState(false);
    const [lastEvent, setLastEvent] = useState<EventPacket | null>(null);
    const [events, setEvents] = useState<EventPacket[]>([]);
    const { isAuthenticated } = useAuthStore();
    const [accessToken, setAccessToken] = useState<string | null>(localStorage.getItem('access_token'));

    useEffect(() => {
        // Keep internal token state in sync with auth state
        if (isAuthenticated) {
            setAccessToken(localStorage.getItem('access_token'));
        } else {
            setAccessToken(null);
        }
    }, [isAuthenticated]);

    useEffect(() => {
        if (!accessToken) return;

        // Use absolute URL or relative if proxied. Ideally use env var.
        const url = `/api/v1/observability/stream?token=${accessToken}`;

        console.log('[GlobalEvents] Connecting to SSE:', url);
        const eventSource = new EventSource(url);

        eventSource.onopen = () => {
            console.log('[GlobalEvents] Connected');
            setIsConnected(true);
            // Synthesize a connection event for the UI
            const connectionEvent: EventPacket = {
                source: 'system',
                event_type: 'system.connection',
                payload: { message: 'Connected to Global Event Stream' },
                timestamp: new Date().toISOString()
            };
            setLastEvent(connectionEvent);
            setEvents(prev => [connectionEvent, ...prev].slice(0, 50));
        };

        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'keepalive') return; // Ignore keepalives

                // Normalize packet structure if needed
                const packet: EventPacket = {
                    source: data.source || 'unknown',
                    event_type: data.event_type || 'unknown',
                    payload: data.payload || {},
                    user_id: data.user_id,
                    timestamp: new Date().toISOString() // Or use server timestamp if provided
                };

                console.log('[GlobalEvents] Received:', packet.event_type);
                setLastEvent(packet);
                setEvents(prev => [packet, ...prev].slice(0, 50));
            } catch (err) {
                console.error('[GlobalEvents] Error parsing event:', err);
            }
        };

        eventSource.onerror = (err) => {
            console.error('[GlobalEvents] SSE Error:', err);
            setIsConnected(false);
            eventSource.close();

            // Retry logic could go here, or depend on React re-mounting
            // For now, let's allow it to reconnect automatically by the browser or manual refresh,
            // but actually EventSource usually retries automatically.
            // However, if we close it, it won't. 
            // Let's NOT close it immediately unless fatal 401?
            // Browsers handle reconnection. We just update state.
            // But standard EventSource behavior on error is to retry.
            // Only close if we are sure it's invalid token.
        };

        return () => {
            console.log('[GlobalEvents] Disconnecting');
            eventSource.close();
            setIsConnected(false);
        };
    }, [accessToken]);

    return (
        <GlobalEventsContext.Provider value={{ isConnected, lastEvent, events }}>
            {children}
        </GlobalEventsContext.Provider>
    );
};

export const useGlobalEvents = () => {
    const context = useContext(GlobalEventsContext);
    if (context === undefined) {
        throw new Error('useGlobalEvents must be used within a GlobalEventsProvider');
    }
    return context;
};
