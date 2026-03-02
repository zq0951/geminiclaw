#!/usr/bin/env python3
import json
import urllib.request
import urllib.parse
import sys

def get_weather(city_name="Shanghai"):
    """Fetch weather information for a specified city using wttr.in JSON API."""
    try:
        url = f"https://wttr.in/{urllib.parse.quote(city_name)}?format=j1"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            current = data['current_condition'][0]
            weather = {
                "city": city_name,
                "temp_C": current['temp_C'],
                "feels_like_C": current['FeelsLikeC'],
                "humidity": current['humidity'],
                "description": current['weatherDesc'][0]['value']
            }
            return weather
    except Exception as e:
        return {"error": str(e), "message": "Failed to fetch weather data."}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        city = sys.argv[1]
    else:
        city = "Shanghai"
        
    print(json.dumps(get_weather(city), indent=2, ensure_ascii=False))
