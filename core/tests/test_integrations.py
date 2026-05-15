from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class IntegrationApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="apiuser", password="testpass123")
        self.client.force_login(self.user)

    @patch("core.web.integrations._fetch_json")
    def test_location_search_returns_normalized_results(self, fetch_json):
        fetch_json.return_value = [
            {
                "name": "Barcelona",
                "display_name": "Barcelona, Catalunya, Spain",
                "lat": "41.3825802",
                "lon": "2.1770730",
                "type": "administrative",
            }
        ]

        response = self.client.get(reverse("api_location_search"), {"q": "Barc"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["results"][0],
            {
                "name": "Barcelona",
                "address": "Barcelona, Catalunya, Spain",
                "latitude": "41.3825802",
                "longitude": "2.1770730",
                "type": "administrative",
            },
        )

    @patch("core.web.integrations._fetch_json")
    def test_weather_forecast_returns_daily_summary(self, fetch_json):
        fetch_json.return_value = {
            "timezone": "Europe/Madrid",
            "daily": {
                "time": ["2026-05-20"],
                "weather_code": [1],
                "temperature_2m_max": [24.2],
                "temperature_2m_min": [13.1],
                "precipitation_probability_max": [10],
            },
        }

        response = self.client.get(
            reverse("api_weather_forecast"),
            {"latitude": "41.3825802", "longitude": "2.1770730", "date": "2026-05-20"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["weather_code"], 1)
        self.assertEqual(response.json()["temperature_max"], 24.2)

    def test_weather_forecast_validates_required_coordinates(self):
        response = self.client.get(
            reverse("api_weather_forecast"),
            {"latitude": "", "longitude": "2.1770730", "date": "2026-05-20"},
        )

        self.assertEqual(response.status_code, 400)
