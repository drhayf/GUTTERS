import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useGlobalEvents } from '../contexts/GlobalEventsContext';


/**
 * Hook to invalidate queries based on received events.
 * 
 * @param queryKey The React Query key(s) to invalidate.
 * @param eventPattern The event type pattern to match (e.g. 'system.worker.*' or 'module.profile_calculated').
 *                     Simple glob matching: '*' matches anything, 'prefix.*' matches prefix.
 */
export const useLiveInvalidation = (queryKey: string[], eventPattern: string | string[]) => {
    const queryClient = useQueryClient();
    const { lastEvent } = useGlobalEvents();

    useEffect(() => {
        if (!lastEvent) return;

        const patterns = Array.isArray(eventPattern) ? eventPattern : [eventPattern];

        const isMatch = patterns.some(pattern => {
            if (pattern === '*') return true;
            if (pattern.endsWith('*')) {
                const prefix = pattern.slice(0, -1);
                return lastEvent.event_type.startsWith(prefix);
            }
            return lastEvent.event_type === pattern;
        });

        if (isMatch) {
            console.log(`[useLiveInvalidation] Invalidating ${queryKey} due to ${lastEvent.event_type}`);
            queryClient.invalidateQueries({ queryKey });
        }
    }, [lastEvent, queryClient, JSON.stringify(queryKey), JSON.stringify(eventPattern)]);
};
