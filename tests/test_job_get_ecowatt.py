from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytest
from test_jobs import job


@pytest.mark.parametrize("response, status_code", [(None, 200), (None, 500), ({"2099-01-01": {"value": 9000, "message": "mock message", "detail": "mock detail"}}, 200)])
def test_get_ecowatt(mocker, job, caplog, requests_mock, response, status_code):
    from config import URL
    start = (datetime.now() - relativedelta(years=3)).strftime("%Y-%m-%d")
    end = (datetime.now() + relativedelta(days=3)).strftime("%Y-%m-%d")

    m_db_get_ecowatt = mocker.patch("models.datasources.database.Database.get_ecowatt")
    m_db_set_ecowatt = mocker.patch("models.datasources.database.Database.set_ecowatt")

    m_db_get_ecowatt.return_value = []
    requests_mock.get(f"{URL}/rte/ecowatt/{start}/{end}", json=response, status_code=status_code)

    job.get_ecowatt()

    assert "INFO     root:dependencies.py:88 RÉCUPÉRATION DES DONNÉES ECOWATT :\n" in caplog.text
    if status_code != 200:
        assert m_db_get_ecowatt.call_count == 1
        assert m_db_set_ecowatt.call_count == 0

        # FIXME: No error is displayed
        assert (
                "ERROR    root:jobs.py:160 Erreur lors de la récupération du statut de la passerelle :\n"
                not in caplog.text
        )

    if status_code == 200:
        if response:
            assert m_db_get_ecowatt.call_count == 1
            assert m_db_set_ecowatt.call_count == 1

            assert (
                    "ERROR    root:ecowatt.py:58 {'error': True, 'description': 'Erreur "
                    "lors de la récupération des données Ecowatt.'}\n"
                    not in caplog.text
            )
        else:
            assert m_db_get_ecowatt.call_count == 1
            assert m_db_set_ecowatt.call_count == 0

            assert (
                "ERROR    root:ecowatt.py:58 {'error': True, 'description': 'Erreur "
                "lors de la récupération des données Ecowatt.'}\n" in caplog.text
            )
