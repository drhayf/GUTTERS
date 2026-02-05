import { useEffect, useState } from 'react'

/**
 * Track keyboard height on mobile devices.
 * 
 * This ensures input stays above keyboard when it opens.
 */
export function useKeyboardHeight() {
    const [keyboardHeight, setKeyboardHeight] = useState(0)

    useEffect(() => {
        const handleResize = () => {
            // On mobile, when keyboard opens, window.innerHeight decreases
            const viewportHeight = window.visualViewport?.height || window.innerHeight
            const windowHeight = window.innerHeight

            const diff = windowHeight - viewportHeight
            setKeyboardHeight(diff > 0 ? diff : 0)
        }

        // Modern browsers
        if (window.visualViewport) {
            window.visualViewport.addEventListener('resize', handleResize)
            window.visualViewport.addEventListener('scroll', handleResize)
        }

        // Fallback
        window.addEventListener('resize', handleResize)

        return () => {
            if (window.visualViewport) {
                window.visualViewport.removeEventListener('resize', handleResize)
                window.visualViewport.removeEventListener('scroll', handleResize)
            }
            window.removeEventListener('resize', handleResize)
        }
    }, [])

    return keyboardHeight
}
