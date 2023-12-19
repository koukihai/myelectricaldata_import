import datetime
import os
from unittest import TestCase, mock

import utils


class TestHomeAssistantWs(TestCase):
    def setUp(self, *args, **kwargs):
        # os.remove(os.path.join(tests_dir, "data", "cache.prod.db"))

        utils.APPLICATION_PATH_DATA = os.path.join(os.getcwd(), "unittests", "myelectricaldata")
        utils.APPLICATION_PATH = os.path.abspath(os.path.join(os.getcwd(), "..", "app"))

        from models.export_home_assistant_ws import HomeAssistantWs
        self.haws = HomeAssistantWs("123")

    def test_send(self):
        self.haws.send("test")

    def test_list_data(self):
        res = self.haws.list_data()
        print(res)

    def test_clear_data(self):
        res = self.haws.clear_data()
        print(res)

    def test_get_data(self):
        res = self.haws.get_data("1", datetime.datetime.now() - datetime.timedelta(days=1), datetime.datetime.now())
        print(res)

    def test_import_data(self):
        self.fail()
