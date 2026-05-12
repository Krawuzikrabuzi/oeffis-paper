# api/api_wrlinien.py
import requests
from requests import RequestException, HTTPError
from utils import get_config, get_logger
from api.base_api import BaseApi
import time

logger = get_logger(__name__)


class WrLinienApiException(Exception):
    pass


class WrLinienApi(BaseApi):

    def _get_update_interval(self):
        return get_config()['api']['wrlinien']['updateInterval']

    def _get_data(self):
        self.data = None
        conf = get_config()

        try:
            res = requests.get(
                'https://www.wienerlinien.at/ogd_realtime/monitor',
                params=[('rbl', rbl) for rbl in conf['api']['wrlinien']['rbls']]
            )
            res.raise_for_status()
        except (RequestException, HTTPError) as e:
            logger.error("Request failed: %s" % e)
            raise

        api_data = res.json()

        if api_data['message']['value'] != 'OK':
            logger.error('[WRL]: NOK. %s' % api_data)
            raise WrLinienApiException("API returns NOK. Please check the message and the API Key.")

        translated_result = []
        for a_s in api_data['data']['monitors']:
            station = {
                'lines': [],
                'name': a_s['locationStop']['properties']['title'],
            }
            for a_s_l in a_s['lines']:
                line = {
                    'name': a_s_l['name'].rjust(3),
                    'direction': a_s_l['towards'],
                    'barrierFree': a_s_l['barrierFree'],
                    'trafficJam': a_s_l['trafficjam'],
                    'departures': []
                }
                for d in a_s_l['departures']['departure']:
                    if d['departureTime']:
                        line['departures'].append(d['departureTime']['countdown'])
                station['lines'].append(line)
            translated_result.append(station)

        self.data = {
            'stations': self._merge_stations_by_name(translated_result),
            'lastUpdate': time.strptime(api_data['message']['serverTime'], '%Y-%m-%dT%H:%M:%S.%f%z')
        }
        logger.debug("retrieved data: %s" % self.data)

    @staticmethod
    def _merge_stations_by_name(result):
        stations = []
        for s in result:
            exists = False
            for d in stations:
                if s['name'] == d['name']:
                    d['lines'].extend(s['lines'])
                    exists = True
            if exists is False:
                stations.append(s)
        return stations