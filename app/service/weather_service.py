import requests
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv
import os
load_dotenv()
from typing import List, Dict
from datetime import datetime
from app.mongo.agri_handlers import WEATHER_HANDLER


def format_tomorrow_result(forecasts: List[Dict], recents: List[Dict]) -> Dict[str, str]:
    """
    Formats Tomorrow.io results into three buckets showing metric progression.
    Example:
    Rain Avg (in mm): 7.98 -> 0.22 (today) -> 1.2 -> ...
    """

    # Merge and sort data chronologically
    all_data = recents + forecasts
    all_data.sort(key=lambda x: x.get("day", ""))

    today_str = datetime.utcnow().strftime("%Y-%m-%d")

    def build_metric_line(title: str, key: str, unit: str = "") -> str:
        parts = []
        for entry in all_data:
            val = entry.get(key, 0)
            date_str = entry.get("day", "")
            if date_str == today_str:
                parts.append(f"{val}{unit} (today)")
            else:
                parts.append(f"{val}{unit}")
        return f"{title}: " + " -> ".join(parts)

    # Buckets
    rain_bucket = [
        build_metric_line("Rain Avg (in mm)", "rain", "mm"),
        build_metric_line("Rain Max (in mm)", "rain_max", "mm"),
        build_metric_line("Rain Min (in mm)", "rain_min", "mm"),
        build_metric_line("Precipitation Probability Max (%)", "precipitation_probability_max", "%"),
        build_metric_line("Precipitation Probability Min (%)", "precipitation_probability_min", "%"),
        build_metric_line("Rain Intensity (in mm)", "rain_intensity", "mm"),
    ]

    temperature_bucket = [
        build_metric_line("Avg Temp (°C)", "temp_avg", "°C"),
        build_metric_line("Max Temp (°C)", "temp_max", "°C"),
        build_metric_line("Min Temp (°C)", "temp_min", "°C"),
        build_metric_line("Humidity (%)", "humidity", "%"),
    ]

    misc_bucket = [
        build_metric_line("Wind Speed (km/h)", "wind_speed", "km/h"),
        build_metric_line("Wind Gust Max (km/h)", "wind_gust_max", "km/h"),
        build_metric_line("Cloud Cover (%)", "cloud_cover", "%"),
    ]

    return {
        "rain": "Following trend represents the daily progression of the precipitation metrics:\n" + "\n".join(rain_bucket),
        "temperature": "Following trend represents the daily progression of the temperature metrics:\n" + "\n".join(temperature_bucket),
        "misc": "Following trend represents the daily progression of the miscellaneous metrics:\n" + "\n".join(misc_bucket)
    }



class TomorrowWeather:
    def __init__(self):
        self.api_key = os.environ["TOMORROW_API_KEY"]
        self.base_url_forecast = "https://api.tomorrow.io/v4/weather/forecast"
        self.base_url_history = "https://api.tomorrow.io/v4/weather/history/recent"

    def _fetch_data(self, url: str, location: str, timesteps: str = "1d") -> Dict:
        params = {
            "location": location,
            "timesteps": timesteps,
            "units": "metric",
            "apikey": self.api_key
        }
        headers = {
            "accept": "application/json",
            "accept-encoding": "deflate, gzip, br"
        }
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()

    def get_forecast(
        self, latitude: float, longitude: float, days: int = 7
    ) -> List[Dict]:
        """
        Get future daily weather forecast for the next `days`.
        """
        location = f"{latitude},{longitude}"
        data = self._fetch_data(self.base_url_forecast, location)
        return self._parse_daily(data, days)

    def get_recent(
        self, latitude: float, longitude: float, days: int = 7
    ) -> List[Dict]:
        """
        Get recent daily weather history for the past `days`.
        """
        location = f"{latitude},{longitude}"
        data = self._fetch_data(self.base_url_history, location)
        return self._parse_daily(data, days)

    def _parse_daily(self, data: Dict, days: int) -> List[Dict]:
        timelines = data.get("timelines", {})
        # The API returns "daily" key inside timelines
        daily_list = timelines.get("daily", [])[:days]
        result = []

        for item in daily_list:
            values = item.get("values", {})
            day_info = {
                "day": item.get("time", "")[:10],
                "temp_avg": values.get("temperatureAvg"),
                "temp_max": values.get("temperatureMax"),
                "temp_min": values.get("temperatureMin"),
                "rain": values.get("rainAccumulationAvg"),
                "rain_max": values.get("rainAccumulationMax"),
                "rain_min": values.get("rainAccumulationMin"),
                "humidity": values.get("humidityAvg"),
                "cloud_cover": values.get("cloudCoverAvg"),
                "wind_speed": values.get("windSpeedAvg"),
                "precipitation_probability_max": values.get("precipitationProbabilityMax"),
                "precipitation_probability_min": values.get("precipitationProbabilityMin"),
                "rain_intensity": values.get("rainIntensityAvg"),
                "wind_gust_max": values.get("windGustMax")
            }
            result.append(day_info)

        return result
    

    def cache_lookup(self, latitude: float, longitude: float, formated=True) -> Optional[Dict]:
        date = datetime.utcnow().strftime("%Y-%m-%d")
        unique_field = "latitude_longitude_date"
        unique_field_value = f"{int(latitude)}_{int(longitude)}_{date}"
        look_up_result = WEATHER_HANDLER.get_by_id(
            unique_field=unique_field,
            value=unique_field_value
        )
        if look_up_result:
            if formated:
                return format_tomorrow_result(
                    forecasts=look_up_result.get("forecasts", []),
                    recents=look_up_result.get("recents", [])
                )
            else:
                return {
                    "forecasts": look_up_result.get("forecasts", []),
                    "recents": look_up_result.get("recents", [])
                }
        return None
    
    def add_weather_data(self, latitude: float, longitude: float, forecasts, recents):
        payload = {
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "latitude": latitude,
            "longitude": longitude,
            "forecasts": forecasts,
            "recents": recents
        }
        WEATHER_HANDLER.add_weather_data(payload)


    def __call__(self, latitude, longitude, days, formated=True) -> Dict[str, str]:
        """
        Fetches weather data for the given latitude and longitude for the next `days`.
        Returns a dictionary with formatted results.
        """
        try:
            look_up_result = self.cache_lookup(latitude, longitude, formated=formated)
            if look_up_result:
                print("Cache hit, returning cached data.")
                return look_up_result
            forecasts = self.get_forecast(latitude, longitude, days)
            recents = self.get_recent(latitude, longitude, days)

            self.add_weather_data(latitude, longitude, forecasts, recents)
            print("Cache miss, fetched new data and stored in cache.")

            if formated:
                return format_tomorrow_result(forecasts, recents)
            else:
                return {
                    "forecasts": forecasts,
                    "recents": recents
                }
        except Exception as e:
            return {"error": str(e)}
        


TOMORROW_WEATHER_SERVICE = TomorrowWeather()