import logging
import os
import tempfile
from contextlib import contextmanager
from unittest import TestCase
from unittest import mock

import pytest as pytest
import yaml

from db_schema import UsagePoints

EXPORT_METHODS = ["export_influxdb", "export_home_assistant_ws", "export_home_assistant", "export_mqtt"]
PER_USAGE_POINT_METHODS = ["get_account_status", "get_contract", "get_addresses", "get_consumption",
                           "get_consumption_detail", "get_production", "get_production_detail",
                           "get_consumption_max_power", "stat_price"] + EXPORT_METHODS
PER_JOB_METHODS = ["get_gateway_status", "get_tempo", "get_ecowatt"]


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
    config = {
        "home_assistant": {"enable": "False"},
        "myelectricaldata": {
            "pdl1": {
                "enable": True,
                "consumption": True,
                "consumption_detail": True,
                "production": True,
                "production_detail": True
            },
            "pdl2": {"enable": False},
            "pdl3": {"enable": False}
        }
    }

    with tempfile.NamedTemporaryFile(delete=True, prefix="config-", suffix=".yaml", mode="w") as fp:
        yaml.dump(config, fp)
        fp.flush()
        print(f"created {fp.name} for testing")
        yield fp.name


def generate_jobs():
    usage_point_ids = [None, "pdl1"]

    from models.jobs import Job

    for usage_point_id in usage_point_ids:
        print(f"Using job with usage point id = {usage_point_id}")
        job = Job(usage_point_id)
        job.wait_job_start = 1
        yield job


@pytest.fixture(params=[None, 'pdl1'])
def job(request):
    from models.jobs import Job

    print(f"Using job with usage point id = {request.param}")
    job = Job(request.param)
    job.wait_job_start = 1
    yield job


# TODO: Extract as a function in main.py to avoid duplication
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


def test_boot(mocker, caplog, job):
    m = mocker.patch('models.jobs.Job.job_import_data')
    expected_logs = ""

    with setenv(DEV="true", DEBUG="true"):
        res = job.boot()
        expected_logs += 'WARNING  root:jobs.py:43 => Import job disable\n'
        assert res is False, "called with DEV or DEBUG should return False"
        assert 0 == m.call_count, "job_import_data should not be called"
        assert expected_logs == caplog.text

    m.return_value = {"status": "Mocked"}
    res = job.boot()
    assert expected_logs == caplog.text
    assert m.return_value["status"] == res
    m.assert_called_once()

    m.reset_mock()


def test_job_import_data(mocker, job, caplog):
    mockers = {}
    for method in PER_JOB_METHODS + PER_USAGE_POINT_METHODS:
        mockers[method] = mocker.patch(f"models.jobs.Job.{method}")

    count_enabled_jobs = len([j for j in job.usage_points if j.enable])
    expected_logs = ""

    res = job.job_import_data(target=None)
    expected_logs += "INFO     root:dependencies.py:86 DÉMARRAGE DU JOB D'IMPORTATION DANS 10S\n"
    assert res["status"] is True
    for method, m in mockers.items():
        if method in PER_JOB_METHODS:
            assert m.call_count == 1
        else:
            assert m.call_count == count_enabled_jobs
        m.reset_mock()

    assert expected_logs in caplog.text


def test_header_generate(job, caplog):
    from dependencies import get_version
    expected_logs = ""
    # header_generate() assumes job.usage_point_config is populated from a side effect
    for job.usage_point_config in job.usage_points:
        assert {'Authorization': '', 'Content-Type': 'application/json', 'call-service': 'myelectricaldata',
                'version': get_version()} == job.header_generate()
    assert expected_logs == caplog.text


@pytest.mark.parametrize("ping_side_effect", [None, Exception("Mocker: Ping failed")])
def test_get_gateway_status(job, caplog, ping_side_effect, mocker):
    m_ping = mocker.patch("models.query_status.Status.ping")
    m_ping.side_effect = ping_side_effect
    m_ping.return_value = {"mocked": "true"}

    res = job.get_gateway_status()

    if ping_side_effect:
        assert "ERROR    root:jobs.py:170 Erreur lors de la récupération du statut de la passerelle :" in caplog.text
    else:
        assert res == m_ping.return_value
        assert "INFO     root:dependencies.py:86 RÉCUPÉRATION DU STATUT DE LA PASSERELLE :" in caplog.text


@pytest.mark.parametrize('status_return_value, is_supported', [
    ({}, True),
    ({'any_key': 'any_value'}, True),
    ({'error': 'only'}, False),
    ({'error': 'with all fields', 'status_code': '5xx', 'description': {'detail': 'proper error'}}, True)
])
@pytest.mark.parametrize('status_side_effect', [None, Exception("Mocker: Status failed")])
def test_get_account_status(mocker, job, caplog, status_side_effect, status_return_value, is_supported):
    m_status = mocker.patch("models.query_status.Status.status")
    m_set_error_log = mocker.patch("models.database.Database.set_error_log")
    mocker.patch('models.jobs.Job.header_generate')

    m_status.side_effect = status_side_effect
    m_status.return_value = status_return_value

    enabled_usage_points = [up for up in job.usage_points if up.enable]
    if not job.usage_point_id:
        expected_count = len(enabled_usage_points)
    else:
        expected_count = 1
        # If job has usage_point_id, get_account_status() expects
        # job.usage_point_config.usage_point_id to be populated from a side effect
        job.usage_point_config = UsagePoints(usage_point_id=job.usage_point_id)

    res = job.get_account_status()

    assert "INFO     root:dependencies.py:86 [PDL1] RÉCUPÉRATION DES INFORMATIONS DU COMPTE :" in caplog.text
    if status_side_effect is None and is_supported:
        assert expected_count == m_set_error_log.call_count
        if status_return_value.get("error"):
            m_set_error_log.assert_called_with('pdl1', '5xx - proper error')
    elif status_side_effect:
        assert "ERROR    root:jobs.py:196 Erreur lors de la récupération des informations du compte" in caplog.text
        assert f"ERROR    root:jobs.py:197 {status_side_effect}" in caplog.text
        # set_error_log is not called in case status() raises an exception
        assert 0 == m_set_error_log.call_count
    elif not is_supported:
        assert "ERROR    root:jobs.py:196 Erreur lors de la récupération des informations du compte" in caplog.text
        assert "ERROR    root:jobs.py:197 'status_code'" in caplog.text
        # set_error_log is not called in case status() returns
        # a dict with an error key but no status_code or description.detail
        assert 0 == m_set_error_log.call_count

    # Ensuring status() is called exactly as many times as enabled usage_points
    # and only once per enabled usage_point
    assert expected_count == m_status.call_count
    for j in enabled_usage_points:
        m_status.assert_called_once_with(usage_point_id=j.usage_point_id)


@pytest.mark.parametrize('method, patch, details, line_no', [
    ("get_contract", "models.query_contract.Contract.get", "Récupération des informations contractuelles", 218),
    ("get_addresses", "models.query_address.Address.get", "Récupération des coordonnées postales", 239),
    ("get_consumption", "models.query_daily.Daily.get", "Récupération de la consommation journalière", 263),
    ("get_consumption_detail", "models.query_detail.Detail.get", "Récupération de la consommation détaillée", 287),
    ("get_production", "models.query_daily.Daily.get", "Récupération de la production journalière", 314),
    ("get_production_detail", "models.query_detail.Detail.get", "Récupération de la production détaillée", 338),
    ("get_consumption_max_power", "models.query_power.Power.get", "Récupération de la puissance maximum journalière", 359),
])
@pytest.mark.parametrize('return_value', [
    {},
    {'any_key': 'any_value'},
    {'error': 'only'},
    {'error': 'with all fields', 'status_code': '5xx', 'description': {'detail': 'proper error'}}
])
@pytest.mark.parametrize('side_effect', [None, Exception("Mocker: call failed")])
def test_get_no_return_check(mocker, job, caplog, side_effect, return_value, method, patch, details, line_no):
    """
    This test covers all methods that call "get" methods from query objects:
    - without checking for their return value
    - without calling set_error_log on failure
    """

    m = mocker.patch(patch)
    m_set_error_log = mocker.patch("models.database.Database.set_error_log")
    mocker.patch('models.jobs.Job.header_generate')

    m.side_effect = side_effect
    m.return_value = return_value

    conf = job.config.usage_point_id_config(job.usage_point_id)
    enabled_usage_points = [up for up in job.usage_points if up.enable]
    if not job.usage_point_id:
        expected_count = len(enabled_usage_points)
    else:
        expected_count = 1
        # If job has usage_point_id, get_account_status() expects
        # job.usage_point_config.usage_point_id to be populated from a side effect
        job.usage_point_config = UsagePoints(
            usage_point_id=job.usage_point_id,
            consumption=conf.get("consumption"),
            consumption_detail=conf.get("consumption_detail"),
            production=conf.get("production"),
            production_detail=conf.get("production_detail")
        )

    res = getattr(job, method)()

    if method == "get_consumption_max_power" and job.usage_point_id is None:
        # This method uses self.usage_point_id instead of usage_point_id
        assert f"INFO     root:dependencies.py:86 [NONE] {details.upper()} :" in caplog.text
    else:
        assert f"INFO     root:dependencies.py:86 [PDL1] {details.upper()} :" in caplog.text

    if side_effect:
        # When get() throws an exception, no error is displayed
        assert f"ERROR    root:jobs.py:{line_no} Erreur lors de la {details.lower()}" in caplog.text
        assert f"ERROR    root:jobs.py:{line_no+1} {side_effect}" in caplog.text
    elif return_value:
        # No matter what get() returns, the method will never log an error
        assert f"ERROR    root:jobs.py:{line_no} Erreur lors de la {details.lower()}" not in caplog.text
        assert f"ERROR    root:jobs.py:{line_no+1} 'status_code'" not in caplog.text

    # Ensuring method is called exactly as many times as enabled usage_points
    assert expected_count == m.call_count

    # set_error_log is never called
    m_set_error_log.assert_not_called()
