# api/api_met.py
import requests
from requests import RequestException, HTTPError
from utils import get_config, get_logger
from api.base_api import BaseApi
import time

logger = get_logger(__name__)


class METApi(BaseApi):

    def _get_update_interval(self):
        return get_config()['api']['met']['updateInterval']

    def _get_data(self):
        conf = get_config()
        lat = conf['api']['met']['lat']
        lon = conf['api']['met']['lon']

        try:
            res = requests.get(
                'https://api.met.no/weatherapi/locationforecast/2.0/complete',
                params={'lat': lat, 'lon': lon},
                headers={'User-Agent': 'oeffis-paper/1.0'}
            )
            res.raise_for_status()
        except (RequestException, HTTPError) as e:
            logger.error("Request failed: %s" % e)
            raise

        api_data = res.json()
        timeseries = api_data['properties']['timeseries']
        updated_at = api_data['properties']['meta']['updated_at']

        weather_data = {
            'lastUpdate': time.strptime(updated_at, '%Y-%m-%dT%H:%M:%SZ'),
            'forecast': []
        }

        # nur die ersten 2 Einträge – das Display zeigt 2 Spalten
        for entry in timeseries[:2]:
            instant = entry['data']['instant']['details']
            next_1h = entry['data'].get('next_1_hours', {})
            symbol_code = next_1h.get('summary', {}).get('symbol_code', 'unknown')
            precipitation = next_1h.get('details', {}).get('precipitation_amount', 0)

            weather_data['forecast'].append({
                'time': {
                    'from': time.strptime(entry['time'], '%Y-%m-%dT%H:%M:%SZ'),
                    'to': time.strptime(entry['time'], '%Y-%m-%dT%H:%M:%SZ'),
                },
                'symbol': {
                    'id': symbol_code,
                    'description': symbol_code
                },
                'precipitation': str(precipitation),
                'wind': {
                    'direction': str(round(instant['wind_from_direction'])),
                    'mps': str(round(instant['wind_speed'], 1)),
                    'description': ''
                },
                'celsius': str(round(instant['air_temperature']))
            })

        logger.debug("retrieved data: %s" % weather_data)
        self.data = weather_data