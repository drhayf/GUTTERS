
import { useCallback } from 'react'

export function useAppBadge() {
    const setBadge = useCallback((count: number) => {
        if ('setAppBadge' in navigator) {
            try {
                navigator.setAppBadge(count)
            } catch (e) {
                console.error('Failed to set app badge', e)
            }
        }
    }, [])

    const clearBadge = useCallback(() => {
        if ('clearAppBadge' in navigator) {
            try {
                navigator.clearAppBadge()
            } catch (e) {
                console.error('Failed to clear app badge', e)
            }
        }
    }, [])

    return { setBadge, clearBadge }
}
