import unittest
from wsgi import app
import requests
import json


class TestFlask(unittest.TestCase):
    def test_index(self):
        tester = app.test_client(self)
        headerss = {"Authorization": "Basic U2VsdmE6U2FtYmF0aA=="}
        response = tester.get("/product", headers=headerss)
        statuscode = response.status_code
        self.assertEqual(statuscode, 200)

    def test_index_content(self):
        tester = app.test_client(self)
        headerss = {"Authorization": "Basic U2VsdmE6U2FtYmF0aA=="}
        response = tester.get("/product", headers=headerss)
        self.assertEqual(response.content_type, "application/json")

    def test_index_content_single_product(self):
        tester = app.test_client(self)
        headerss = {"Authorization": "Basic U2VsdmE6U2FtYmF0aA=="}
        response = tester.get("/product/2", headers=headerss)
        self.assertEqual(response.content_type, "application/json")

    def test_index_content_empty_or_not(self):
        url = "http://127.0.0.1:5000/product"
        session = requests.session()
        headerss = {"Authorization": "Basic U2VsdmE6U2FtYmF0aA=="}
        response = session.get(url, headers=headerss)
        result = response.json()
        for item in result:
            if len(item) != 0:
                self.assertTrue(item)

    def test_get_content(self):
        url = "http://127.0.0.1:5000/product"
        session = requests.session()
        headerss = {"Authorization": "Basic U2VsdmE6U2FtYmF0aA=="}
        response = session.get(url, headers=headerss)
        result = response.json()
        status = response.status_code
        self.assertEqual(status, 200)


if __name__ == "main":
    unittest.main()
