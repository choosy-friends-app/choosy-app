import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse


HTTP_TIMEOUT_SECONDS = 7
NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def _fetch_json(url, params):
    query = urlencode(params)
    request = Request(
        f"{url}?{query}",
        headers={
            "Accept": "application/json",
            "User-Agent": "ChoosyApp/1.0 (https://github.com/choosy-friends-app/choosy-app)",
        },
    )
    with urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


@login_required
def api_location_search(request):
    query = (request.GET.get("q") or "").strip()
    if len(query) < 3:
        return JsonResponse({"results": []})

    try:
        payload = _fetch_json(
            NOMINATIM_SEARCH_URL,
            {
                "q": query,
                "format": "jsonv2",
                "addressdetails": 1,
                "limit": 6,
                "accept-language": "en",
            },
        )
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return JsonResponse(
            {"error": "Location search is temporarily unavailable."},
            status=502,
        )

    results = []
    for item in payload[:6]:
        if not item.get("lat") or not item.get("lon") or not item.get("display_name"):
            continue
        results.append(
            {
                "name": item.get("name") or item["display_name"].split(",")[0],
                "address": item["display_name"],
                "latitude": item["lat"],
                "longitude": item["lon"],
                "type": item.get("type", ""),
            }
        )

    return JsonResponse({"results": results})


@login_required
def api_weather_forecast(request):
    raw_latitude = request.GET.get("latitude")
    raw_longitude = request.GET.get("longitude")
    date = (request.GET.get("date") or "").strip()

    try:
        latitude = Decimal(raw_latitude)
        longitude = Decimal(raw_longitude)
    except (InvalidOperation, TypeError):
        return JsonResponse({"error": "A valid selected location is required."}, status=400)

    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return JsonResponse({"error": "A valid plan date is required."}, status=400)

    try:
        payload = _fetch_json(
            OPEN_METEO_FORECAST_URL,
            {
                "latitude": str(latitude),
                "longitude": str(longitude),
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "timezone": "auto",
                "start_date": date,
                "end_date": date,
            },
        )
    except HTTPError as exc:
        if exc.code == 400:
            return JsonResponse(
                {
                    "error": "Forecasts are only available for dates inside Open-Meteo's supported forecast window.",
                    "code": "date_out_of_range",
                },
                status=422,
            )
        return JsonResponse({"error": "Weather forecast is temporarily unavailable."}, status=502)
    except (URLError, TimeoutError, json.JSONDecodeError):
        return JsonResponse({"error": "Weather forecast is temporarily unavailable."}, status=502)

    if payload.get("error"):
        return JsonResponse(
            {
                "error": payload.get("reason") or "Weather forecast is unavailable for this date.",
                "code": "forecast_unavailable",
            },
            status=422,
        )

    daily = payload.get("daily") or {}
    if not daily.get("time"):
        return JsonResponse({"error": "Weather forecast is unavailable for this date."}, status=422)

    return JsonResponse(
        {
            "date": daily["time"][0],
            "weather_code": daily.get("weather_code", [None])[0],
            "temperature_max": daily.get("temperature_2m_max", [None])[0],
            "temperature_min": daily.get("temperature_2m_min", [None])[0],
            "precipitation_probability": daily.get("precipitation_probability_max", [None])[0],
            "timezone": payload.get("timezone", ""),
        }
    )
