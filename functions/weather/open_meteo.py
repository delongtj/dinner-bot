import requests
from datetime import datetime

# WMO Weather interpretation codes to human-readable conditions
WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def geocode_zip(zip_code: str) -> dict:
    """
    Geocode a US zip code using Open-Meteo's geocoding API.
    Returns dict with name, latitude, longitude.
    """
    resp = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": zip_code, "count": 1, "language": "en", "format": "json"},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    results = data.get("results")
    if not results:
        raise ValueError(f"Could not geocode zip code: {zip_code}")

    loc = results[0]
    return {
        "name": f"{loc.get('name', '')}, {loc.get('admin1', '')}",
        "latitude": loc["latitude"],
        "longitude": loc["longitude"],
    }


def get_weekly_forecast(zip_code: str) -> dict:
    """
    Get a 7-day weather forecast for a US zip code.

    Returns:
        {
            "location": "Atlanta, Georgia",
            "forecast": [
                {
                    "date": "2026-02-20",
                    "day": "Friday",
                    "high_f": 65,
                    "low_f": 42,
                    "condition": "Partly cloudy",
                    "precipitation_chance": 10
                },
                ...
            ]
        }
    """
    geo = geocode_zip(zip_code)

    resp = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": geo["latitude"],
            "longitude": geo["longitude"],
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code",
            "temperature_unit": "fahrenheit",
            "timezone": "auto",
            "forecast_days": 7,
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    daily = data.get("daily", {})
    dates = daily.get("time", [])
    highs = daily.get("temperature_2m_max", [])
    lows = daily.get("temperature_2m_min", [])
    precip = daily.get("precipitation_probability_max", [])
    codes = daily.get("weather_code", [])

    forecast = []
    for i, date_str in enumerate(dates):
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        forecast.append({
            "date": date_str,
            "day": DAY_NAMES[dt.weekday()],
            "high_f": round(highs[i]) if i < len(highs) else None,
            "low_f": round(lows[i]) if i < len(lows) else None,
            "condition": WMO_CODES.get(codes[i], "Unknown") if i < len(codes) else "Unknown",
            "precipitation_chance": round(precip[i]) if i < len(precip) else None,
        })

    return {
        "location": geo["name"],
        "forecast": forecast,
    }
