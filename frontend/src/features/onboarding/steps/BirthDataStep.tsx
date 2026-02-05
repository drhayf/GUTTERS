import { useState } from 'react'
import { useOnboardingStore } from '@/stores/onboardingStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Calendar, Clock, MapPin, Loader2 } from 'lucide-react'
import { Checkbox } from '@/components/ui/checkbox'
import api from '@/lib/api'

export default function BirthDataStep() {
    const { setStep, setBirthData } = useOnboardingStore()
    const [isLoading, setIsLoading] = useState(false)
    const [geocodingError, setGeocodingError] = useState<string | null>(null)
    const [formData, setFormData] = useState({
        date: '',
        time: '',
        location: '',
        timeUnknown: false
    })

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setIsLoading(true)
        setGeocodingError(null)

        try {
            // 1. Geocode the location
            let lat, lng, timezone, resolvedLocation

            try {
                const { data: geoData } = await api.post('/api/v1/profile/geocode', {
                    location: formData.location
                })
                lat = geoData.latitude
                lng = geoData.longitude
                timezone = geoData.timezone
                resolvedLocation = geoData.address
            } catch (err) {
                // Fallback or Error? 
                // User requested "Maximum Scrutiny", so we should error if we can't resolve.
                console.error("Geocoding failed", err)
                setGeocodingError("Could not resolve this location. Please be more specific (e.g. 'City, Country').")
                setIsLoading(false)
                return
            }

            const payload = {
                birth_date: formData.date,
                birth_time: formData.timeUnknown ? null : formData.time,
                birth_location: resolvedLocation || formData.location,
                latitude: lat,
                longitude: lng,
                timezone: timezone,
                time_unknown: formData.timeUnknown
            }

            // 2. Save birth data
            await api.post('/api/v1/profile/birth-data', payload)

            setBirthData(payload as any)
            setStep('calculation')

        } catch (error) {
            console.error(error)
            setGeocodingError("An unexpected error occurred.")
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <div className="flex flex-col gap-6 w-full max-w-md mx-auto">
            <div className="text-center mb-4">
                <h2 className="text-3xl font-bold mb-2">Cosmic Coordinates</h2>
                <p className="text-muted-foreground">Precise time enables Human Design & House calculations.</p>
            </div>

            <form onSubmit={handleSubmit} className="flex flex-col gap-6">
                <div className="space-y-2">
                    <Label htmlFor="date">Date of Birth</Label>
                    <div className="relative">
                        <Calendar className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                        <Input
                            id="date"
                            type="date"
                            required
                            className="pl-10"
                            value={formData.date}
                            onChange={e => setFormData({ ...formData, date: e.target.value })}
                        />
                    </div>
                </div>

                <div className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="time">Time of Birth</Label>
                        <div className="relative">
                            <Clock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                            <Input
                                id="time"
                                type="time"
                                className="pl-10"
                                disabled={formData.timeUnknown}
                                value={formData.time}
                                onChange={e => setFormData({ ...formData, time: e.target.value })}
                                required={!formData.timeUnknown}
                            />
                        </div>
                    </div>

                    <div className="flex items-center space-x-2">
                        <Checkbox
                            id="unknown"
                            checked={formData.timeUnknown}
                            onCheckedChange={(checked) => setFormData({ ...formData, timeUnknown: !!checked, time: '' })}
                        />
                        <Label htmlFor="unknown" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                            I don't know my birth time
                        </Label>
                    </div>
                </div>

                <div className="space-y-2">
                    <Label htmlFor="location">Place of Birth (City, Country)</Label>
                    <div className="relative">
                        <MapPin className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                        <Input
                            id="location"
                            placeholder="e.g. London, UK"
                            required
                            className="pl-10"
                            value={formData.location}
                            onChange={e => setFormData({ ...formData, location: e.target.value })}
                        />
                    </div>
                    {geocodingError && (
                        <p className="text-sm text-destructive font-medium">{geocodingError}</p>
                    )}
                </div>

                <Button type="submit" size="lg" className="mt-4" disabled={isLoading}>
                    {isLoading ? (
                        <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Verifying Coordinates...
                        </>
                    ) : (
                        "Calculate Profile"
                    )}
                </Button>
            </form>
        </div>
    )
}
