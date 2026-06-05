import os
import time
import requests
from typing import Optional

AMADEUS_TOKEN_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
AMADEUS_FLIGHT_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"


class AmadeusClient:
    _token: Optional[str] = None
    _token_expires_at: float = 0.0
    _cache: dict = {}

    def __init__(self):
        self.api_key = os.getenv("AMADEUS_API_KEY", "")
        self.api_secret = os.getenv("AMADEUS_API_SECRET", "")

    def _get_token(self) -> Optional[str]:
        if not self.api_key or not self.api_secret:
            return None
        if AmadeusClient._token and time.time() < AmadeusClient._token_expires_at:
            return AmadeusClient._token
        try:
            resp = requests.post(
                AMADEUS_TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.api_key,
                    "client_secret": self.api_secret,
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            AmadeusClient._token = data["access_token"]
            AmadeusClient._token_expires_at = time.time() + data.get("expires_in", 1799) - 30
            return AmadeusClient._token
        except Exception:
            return None

    def search_flights(self, origin: str, destination: str, date: str, adults: int = 1) -> list[dict]:
        cache_key = f"{origin}-{destination}-{date}-{adults}"
        if cache_key in AmadeusClient._cache:
            return AmadeusClient._cache[cache_key]

        token = self._get_token()
        if not token:
            return self._fallback_data(origin, destination, date)

        try:
            resp = requests.get(
                AMADEUS_FLIGHT_URL,
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "originLocationCode": origin,
                    "destinationLocationCode": destination,
                    "departureDate": date,
                    "adults": adults,
                    "max": 5,
                    "currencyCode": "KRW",
                },
                timeout=15,
            )
            resp.raise_for_status()
            raw_offers = resp.json().get("data", [])
            results = self._parse_offers(raw_offers)
            AmadeusClient._cache[cache_key] = results
            return results
        except Exception:
            return self._fallback_data(origin, destination, date)

    def _parse_offers(self, raw_offers: list) -> list[dict]:
        results = []
        for offer in raw_offers[:3]:
            try:
                itinerary = offer["itineraries"][0]
                segment = itinerary["segments"][0]
                price = offer["price"]["grandTotal"]
                results.append({
                    "airline": segment["carrierCode"],
                    "flight_number": f"{segment['carrierCode']}{segment['number']}",
                    "departure": segment["departure"]["at"],
                    "arrival": segment["arrival"]["at"],
                    "price_krw": int(float(price)),
                    "duration": itinerary.get("duration", ""),
                })
            except (KeyError, ValueError, IndexError):
                continue
        return results

    def _fallback_data(self, origin: str, destination: str, date: str) -> list[dict]:
        return [
            {
                "airline": "KE",
                "flight_number": "KE001",
                "departure": f"{date}T09:00:00",
                "arrival": f"{date}T11:30:00",
                "price_krw": 320000,
                "duration": "PT2H30M",
            },
            {
                "airline": "OZ",
                "flight_number": "OZ201",
                "departure": f"{date}T14:00:00",
                "arrival": f"{date}T16:40:00",
                "price_krw": 285000,
                "duration": "PT2H40M",
            },
            {
                "airline": "7C",
                "flight_number": "7C101",
                "departure": f"{date}T18:30:00",
                "arrival": f"{date}T21:00:00",
                "price_krw": 198000,
                "duration": "PT2H30M",
            },
        ]
