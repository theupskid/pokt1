import datetime
import json
import os
import time
import unittest
 
from sandwalker import create_app
from sandwalker import models, routes


class BasicTests(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        with self.app.app_context():
            models.db.create_all()
            self.test_app = self.app.test_client()
            models.db.session.add(
                models.TimelineEntry(account='84', block=25000, amount=1000000, time=datetime.date.fromisoformat('2021-05-21')))
            models.db.session.commit()
 
    def tearDown(self):
        with self.app.app_context():
            models.db.session.close()
            models.db.drop_all()

    def test_home(self):
        response = self.test_app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        assert 'Current Height is <b>25000</b>' in str(response.data)

    def test_explorer(self):
        response = self.test_app.get('/explorer', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_about(self):
        response = self.test_app.get('/about', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_resources(self):
        response = self.test_app.get('/resources', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        assert 'Download Daily Dump' in str(response.data)

    def test_explore_nok(self):
        response = self.test_app.get('/explore', follow_redirects=True)
        self.assertEqual(response.status_code, 404)

    def test_explore_not_found(self):
        response = self.test_app.get('/explore/42', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        assert 'No reward were found for 42' in str(response.data)

    def test_explore_rewards_found(self):
        response = self.test_app.get('/explore/84', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        assert '1 rewards earned' in str(response.data)
        assert '1.000 <small class="exp">pokt</small> minted' in str(response.data)
        assert '2021-05-21' in str(response.data)

    def test_csv_export(self):
        response = self.test_app.get('/csv/account/84', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b'block_time,block_height,reward_upkt\r\n2021-05-21 00:00:00,25000,1000000\r\n', response.data)

    def test_api_rewards_all(self):
        response = self.test_app.post(
            '/api/rewards', data=json.dumps(dict({'accounts': ['84']})), content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {
            'accounts': {
                '84': [
                    {'block': 25000,
                     'reward': 1000000,
                     'time': 'Thu, 20 May 2021 23:00:00 GMT'
                     }
                ]
            }})

    def test_api_block(self):
        response = self.test_app.post(
            '/api/block', data=json.dumps(dict({'block': 25000})), content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'entries': [{'account': '84', 'reward': 1000000, 'time': 'Thu, 20 May 2021 23:00:00 GMT'}]})

    def test_api_height(self):
        response = self.test_app.get('/api/height')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'height': 24999})

    def test_reporter_ok_empty(self):
        response = self.test_app.get('/reporter', follow_redirects=True)
        assert 'List of Pocket Account Identifiers' in str(response.data)

    def test_reporter_ok_get(self):
        response = self.test_app.get('/reporter?accounts=84 ', follow_redirects=True)
        assert '<h3>Summary of Pocket Accounts (<small>1</small>)</h3>' in str(response.data)
        assert '2021-05-01' in str(response.data)
        assert 'Direct Link' in str(response.data)
        assert 'Download CSV' in str(response.data)

    def test_reporter_ok_post(self):
        response = self.test_app.post('/reporter', data={'accounts': '84'}, follow_redirects=True)
        assert '<h3>Summary of Pocket Accounts (<small>1</small>)</h3>' in str(response.data)
        assert '2021-05-01' in str(response.data)
        assert 'Direct Link' in str(response.data)
        assert 'Download CSV' in str(response.data)

    def test_csv_overview(self):
        response = self.test_app.post('/csv/overview', data={'accounts': '84 84'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b'month,account,total_upkt\r\n2021-05-01,84,1000000.0\r\n', response.data)


if __name__ == "__main__":
    unittest.main()
