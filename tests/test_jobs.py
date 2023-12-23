import logging
import os
import tempfile
from contextlib import contextmanager
from unittest import TestCase
from unittest import mock

import pytest as pytest
import yaml

from db_schema import UsagePoints


@contextmanager
def setenv(**envvars):
    old_env = os.environ.copy()
    try:
        for envvar, value in envvars.items():
            os.environ[envvar] = value
        yield
    finally:
        os.environ = old_env


@contextmanager
def mock_config():
    config = {"home_assistant": {"enable": "False"}, "myelectricaldata": {"pdl1": {"enable": False}}}
    with tempfile.NamedTemporaryFile(delete=True, prefix="config-", suffix=".yaml", mode="w") as fp:
        yaml.dump(config, fp)
        fp.flush()
        print(f"created {fp.name} for testing")
        yield fp.name


def generate_jobs():
    from models.jobs import Job

    params = [None, "pdl1"]
    for param in params:
        job = Job(param)
        job.wait_job_start = 0
        yield job


# TODO: Extract as a function in main.py
def copied_from_main():
    from init import CONFIG, DB
    usage_point_list = []
    if CONFIG.list_usage_point() is not None:
        for upi, upi_data in CONFIG.list_usage_point().items():
            logging.info(f"{upi}")
            DB.set_usage_point(upi, upi_data)
            usage_point_list.append(upi)
            logging.info("  => Success")
    else:
        logging.warning("Aucun point de livraison détecté.")

    DB.clean_database(usage_point_list)


@pytest.fixture(scope="session", autouse=True)
def update_paths():
    project_root = os.path.abspath(os.path.join(os.path.realpath(__file__), "..", ".."))
    app_path = os.path.join(project_root, "app")
    data_path = os.path.join(project_root, "tests", "data")
    with mock_config() as config_path:
        with setenv(APPLICATION_PATH=app_path, APPLICATION_PATH_DATA=data_path, CONFIG_PATH=config_path):
            copied_from_main()
            yield


class TestJob(TestCase):
    @mock.patch('models.jobs.Job.job_import_data')
    def test_boot(self, m: mock.Mock):
        for job in generate_jobs():
            print(job)
            with setenv(DEV="true", DEBUG="true"), self.assertLogs(logging.getLogger()) as logs:
                res = job.boot()
                self.assertFalse(res), "called with DEV or DEBUG should return False"
                self.assertEqual(0, m.call_count), "job_import_data should not be called"
                self.assertEqual(['WARNING:root:=> Import job disable'], logs.output)

            m.return_value = {"status": "Mocked"}
            with self.assertNoLogs(logging.getLogger()):
                res = job.boot()
                self.assertEqual(m.return_value["status"], res)
                m.assert_called_once()

            m.reset_mock()

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
        for job in generate_jobs():
            with self.assertLogs(logging.getLogger()) as logs:
                res = job.job_import_data(target=None)
                self.assertTrue(res["status"])
                for m in args:
                    if m._mock_name in ["get_gateway_status", "get_tempo", "get_ecowatt"]:
                        m.assert_called_once()
                    else:
                        self.assertEqual(len([j for j in job.usage_points if j.enable]), m.call_count)
                    m.reset_mock()
                self.assertIn("INFO:root:DÉMARRAGE DU JOB D'IMPORTATION DANS 10S", logs.output)

    def test_header_generate(self):
        from dependencies import get_version
        for job in generate_jobs():
            with self.assertNoLogs(logging.getLogger()):
                # self.header_generate() assumes self.usage_point_config is overwritten
                for job.usage_point_config in job.usage_points:
                    self.assertDictEqual(
                        {'Authorization': '', 'Content-Type': 'application/json', 'call-service': 'myelectricaldata',
                         'version': get_version()},
                        job.header_generate())

    @mock.patch('models.jobs.Job.header_generate')
    def test_get_gateway_status(self, _):
        for job in generate_jobs():
            with self.assertLogs(logging.getLogger()) as logs:
                res = job.get_gateway_status()
                self.assertTrue(res["status"])
                self.assertIn("INFO:root:RÉCUPÉRATION DU STATUT DE LA PASSERELLE :", logs.output)
                self.assertIn("INFO:root:status: True", logs.output)
