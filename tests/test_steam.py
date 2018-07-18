from unittest import TestCase
from unittest.mock import Mock, patch
from picker import Steam
# from unittest.mock import Mock, patch
import configparser


class TestSteam(TestCase):
    @classmethod
    def setUpClass(cls):
        settings = configparser.ConfigParser()
        settings.read('settings.ini')
        cls.steam = Steam(settings['steam'])
        cls.mock_call_patcher = patch('picker.steam.WebAPI.call')
        cls.mock_call = cls.mock_call_patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls.mock_call_patcher.stop()

    def test_resolve_vanity_url(self):
        test_data = {'https://steamcommunity.com/profiles/6459068394824823': {'response': {'success': 42, 'message': 'No match'}},
                'https://steamcommunity.com/id/izdwuut/': {'response': {'steamid': '76561198011689582', 'success': 1}}}

        def side_effect(method_path, **kwargs):
            return test_data[kwargs['vanityurl']]

        self.mock_call.side_effect = side_effect
        for url, response in test_data.items():
            self.assertDictEqual(self.steam.resolve_vanity_url(url), response['response'])
            self.mock_call.assert_called_with('ISteamUser.ResolveVanityURL', vanityurl=url)
