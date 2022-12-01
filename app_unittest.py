import unittest
from app import app
import requests

class TestFlask(unittest.TestCase):

    def test_index(self):
        tester = app.test_client(self)
        response = tester.get('/product')
        statuscode = response.status_code
        self.assertEqual(statuscode,200)

    def test_index_content(self):
        tester = app.test_client(self)
        response = tester.get('/product')
        self.assertEqual(response.content_type, 'application/json')

    def test_get_content(self):
        url ='http://127.0.0.1:5000/product'
        session = requests.session()
        headerss={'Authorization': 'Basic U2VsdmE6U2FtYmF0aA=='}
        response = session.get(url,headers=headerss)
        print (response.json())
        status = response.status_code
        self.assertEqual(status, 200)

if __name__ == "main":
    unittest.main() 