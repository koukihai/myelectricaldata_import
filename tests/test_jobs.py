import os
from unittest import TestCase
from unittest import mock

import pytest as pytest

from db_schema import UsagePoints

import utils


@pytest.fixture(scope="session", autouse=True)
def update_paths():
    utils.CONFIG_PATH = os.path.abspath(os.path.join(os.getcwd(), "..", "config.exemple.yaml"))
    utils.APPLICATION_PATH_DATA = os.path.join(os.getcwd(), "unittests", "myelectricaldata")
    utils.APPLICATION_PATH = os.path.abspath(os.path.join(os.getcwd(), "..", "app"))
    with mock.patch('models.config.Config.storage_config') as mock_storage:
        mock_storage.return_value = "sqlite:///abcd.db"
        yield
    os.remove("abcd.db")


class TestJob(TestCase):
    def setUp(self) -> None:
        from models.jobs import Job
        self.job = Job()

    @mock.patch('models.jobs.Job.job_import_data')
    def test_boot(self, _):
        self.job.boot()

    @mock.patch('models.jobs.Job.export_influxdb')
    @mock.patch('models.jobs.Job.export_home_assistant_ws')
    @mock.patch('models.jobs.Job.export_home_assistant')
    @mock.patch('models.jobs.Job.export_mqtt')
    @mock.patch('models.jobs.Job.stat_price')
    @mock.patch('models.jobs.Job.get_consumption_max_power')
    @mock.patch('models.jobs.Job.get_production_detail')
    @mock.patch('models.jobs.Job.get_production')
    @mock.patch('models.jobs.Job.get_consumption_detail')
    @mock.patch('models.jobs.Job.get_consumption')
    @mock.patch('models.jobs.Job.get_addresses')
    @mock.patch('models.jobs.Job.get_contract')
    @mock.patch('models.jobs.Job.get_account_status')
    @mock.patch('models.jobs.Job.get_ecowatt')
    @mock.patch('models.jobs.Job.get_tempo')
    @mock.patch('models.jobs.Job.get_gateway_status')
    def test_job_import_data(self, *args: mock.Mock):
        res = self.job.job_import_data(target=None)
        print(res)
        self.assertTrue(res["status"])
        for m in args:
            if m._mock_name in ["get_gateway_status", "get_tempo", "get_ecowatt"]:
                m.assert_called_once()
            else:
                self.assertEqual(len(self.job.usage_points), m.call_count)

    def test_header_generate(self):
        usage_points = [UsagePoints()]
        for usage_point in usage_points:
            print(self.job.header_generate(usage_point))

    @mock.patch('models.jobs.Job.header_generate')
    def test_get_gateway_status(self, _):
        res = self.job.get_gateway_status()
        self.assertTrue(res["status"])

    def test_get_account_status(self):
        all_valid = all([a['valid'] for a in self.job.get_account_status()])
        self.assertTrue(all_valid)

    def test_get_contract(self):
        print(self.job.get_contract())

    def test_get_addresses(self):
        self.fail()

    def test_get_consumption(self):
        self.fail()

    def test_get_consumption_detail(self):
        self.fail()

    def test_get_production(self):
        self.fail()

    def test_get_production_detail(self):
        self.fail()

    def test_get_consumption_max_power(self):
        self.fail()

    def test_get_tempo(self):
        self.fail()

    def test_get_ecowatt(self):
        self.fail()

    def test_stat_price(self):
        self.fail()

    def test_export_home_assistant(self):
        self.fail()

    def test_export_home_assistant_ws(self):
        self.fail()

    def test_export_influxdb(self):
        self.fail()

    def test_export_mqtt(self):
        self.fail()
