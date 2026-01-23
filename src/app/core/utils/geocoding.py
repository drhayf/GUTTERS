"""
GUTTERS Geocoding Utilities

Location geocoding and timezone resolution for accurate cosmic calculations.
Birth location accuracy is critical for astrology - even small errors in
coordinates can significantly affect house placements and ascendant.

Uses:
- Nominatim (OpenStreetMap) for geocoding (free, TOS: 1 req/sec)
- TimezoneFinder for timezone resolution from coordinates
"""
import logging
import time
from functools import lru_cache
from typing import Any

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from timezonefinder import TimezoneFinder

logger = logging.getLogger(__name__)

# Rate limiting: track last request time
_last_request_time: float = 0.0

# Reusable geocoder and timezone finder instances
_geocoder: Nominatim | None = None
_timezone_finder: TimezoneFinder | None = None


def _get_geocoder() -> Nominatim:
    """Get or create the Nominatim geocoder instance."""
    global _geocoder
    if _geocoder is None:
        _geocoder = Nominatim(
            user_agent="gutters-cosmic-intelligence",
            timeout=10
        )
    return _geocoder


def _get_timezone_finder() -> TimezoneFinder:
    """Get or create the TimezoneFinder instance."""
    global _timezone_finder
    if _timezone_finder is None:
        _timezone_finder = TimezoneFinder()
    return _timezone_finder


def _rate_limit() -> None:
    """
    Enforce Nominatim TOS rate limit (1 request per second).
    
    Blocks if called within 1 second of last request.
    """
    global _last_request_time
    current_time = time.time()
    elapsed = current_time - _last_request_time
    
    if elapsed < 1.0:
        sleep_time = 1.0 - elapsed
        logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
        time.sleep(sleep_time)
    
    _last_request_time = time.time()


def get_timezone_from_coords(latitude: float, longitude: float) -> str:
    """
    Get IANA timezone identifier from coordinates.
    
    Args:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        
    Returns:
        IANA timezone string (e.g., "America/New_York", "Europe/London")
        
    Raises:
        ValueError: If coordinates are invalid or timezone cannot be determined
        
    Example:
        >>> tz = get_timezone_from_coords(40.7128, -74.0060)
        >>> print(tz)
        'America/New_York'
    """
    tf = _get_timezone_finder()
    timezone = tf.timezone_at(lat=latitude, lng=longitude)
    
    if timezone is None:
        raise ValueError(
            f"Could not determine timezone for coordinates: {latitude}, {longitude}"
        )
    
    return timezone


def geocode_location(location_str: str) -> dict[str, Any] | None:
    """
    Geocode a location string to coordinates and timezone.
    
    Uses Nominatim (OpenStreetMap) for geocoding. Rate limited to 1 req/sec
    per Nominatim Terms of Service.
    
    Args:
        location_str: Human-readable location (e.g., "San Francisco, CA, USA")
        
    Returns:
        Dict with address, latitude, longitude, timezone, or None if not found:
        {
            "address": "San Francisco, California, USA",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "timezone": "America/Los_Angeles"
        }
        
    Example:
        >>> result = geocode_location("Paris, France")
        >>> print(f"{result['latitude']}, {result['longitude']}")
        '48.8566, 2.3522'
        >>> print(result['timezone'])
        'Europe/Paris'
    """
    if not location_str or not location_str.strip():
        logger.warning("Empty location string provided")
        return None
    
    geocoder = _get_geocoder()
    
    try:
        # Enforce rate limit
        _rate_limit()
        
        # Geocode the location
        location = geocoder.geocode(location_str, addressdetails=True)
        
        if location is None:
            logger.warning(f"Could not geocode location: {location_str}")
            return None
        
        latitude = float(location.latitude)
        longitude = float(location.longitude)
        
        # Get timezone from coordinates
        try:
            timezone = get_timezone_from_coords(latitude, longitude)
        except ValueError as e:
            logger.warning(f"Could not determine timezone: {e}")
            timezone = "UTC"  # Fallback
        
        result = {
            "address": location.address,
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone,
        }
        
        logger.info(f"Geocoded '{location_str}' -> {latitude:.4f}, {longitude:.4f} ({timezone})")
        return result
        
    except GeocoderTimedOut:
        logger.error(f"Geocoding timed out for: {location_str}")
        return None
    except GeocoderServiceError as e:
        logger.error(f"Geocoding service error for '{location_str}': {e}")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error geocoding '{location_str}': {e}")
        return None


def reverse_geocode(latitude: float, longitude: float) -> str | None:
    """
    Convert coordinates to a human-readable address.
    
    Uses Nominatim (OpenStreetMap) for reverse geocoding. Rate limited to
    1 req/sec per Nominatim Terms of Service.
    
    Args:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        
    Returns:
        Formatted address string, or None if not found
        
    Example:
        >>> address = reverse_geocode(37.7749, -122.4194)
        >>> print(address)
        'San Francisco, California, USA'
    """
    geocoder = _get_geocoder()
    
    try:
        # Enforce rate limit
        _rate_limit()
        
        # Reverse geocode
        location = geocoder.reverse((latitude, longitude), language="en")
        
        if location is None:
            logger.warning(f"Could not reverse geocode: {latitude}, {longitude}")
            return None
        
        logger.info(f"Reverse geocoded {latitude:.4f}, {longitude:.4f} -> '{location.address}'")
        return location.address
        
    except GeocoderTimedOut:
        logger.error(f"Reverse geocoding timed out for: {latitude}, {longitude}")
        return None
    except GeocoderServiceError as e:
        logger.error(f"Reverse geocoding service error: {e}")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error reverse geocoding: {e}")
        return None


@lru_cache(maxsize=256)
def geocode_location_cached(location_str: str) -> tuple[str, float, float, str] | None:
    """
    Cached version of geocode_location for frequently used locations.
    
    Returns tuple instead of dict for hashability.
    
    Args:
        location_str: Human-readable location
        
    Returns:
        Tuple of (address, latitude, longitude, timezone) or None
        
    Example:
        >>> result = geocode_location_cached("Tokyo, Japan")
        >>> address, lat, lon, tz = result
    """
    result = geocode_location(location_str)
    if result is None:
        return None
    
    return (
        result["address"],
        result["latitude"],
        result["longitude"],
        result["timezone"],
    )
