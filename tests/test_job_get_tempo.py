from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytest
from test_jobs import job


@pytest.mark.parametrize("response, status_code", [(None, 200), (None, 500), ({"2099-01-01": "turquoise"}, 200)])
def test_get_tempo(mocker, job, caplog, requests_mock, response, status_code):
    from config import URL
    start = (datetime.now() - relativedelta(years=3)).strftime("%Y-%m-%d")
    end = (datetime.now() + relativedelta(days=2)).strftime("%Y-%m-%d")

    m_db_get_tempo = mocker.patch("models.datasources.database.Database.get_tempo")
    m_db_set_tempo_config = mocker.patch("models.datasources.database.Database.set_tempo_config")
    m_db_set_tempo = mocker.patch("models.datasources.database.Database.set_tempo")

    requests_mock.get(f"{URL}/rte/tempo/{start}/{end}", json=response, status_code=status_code)
    requests_mock.get(f"{URL}/edf/tempo/days", json=response, status_code=status_code)
    requests_mock.get(f"{URL}/edf/tempo/price", json=response, status_code=status_code)

    job.get_tempo()

    assert "INFO     root:dependencies.py:88 RÉCUPÉRATION DES DONNÉES TEMPO :\n" in caplog.text
    if status_code != 200:
        assert m_db_get_tempo.call_count == 1
        assert m_db_set_tempo.call_count == 0
        assert m_db_set_tempo_config.call_count == 0

        # FIXME: No error is displayed
        assert (
                "ERROR    root:jobs.py:160 Erreur lors de la récupération du statut de la passerelle :\n"
                not in caplog.text
        )

    if status_code == 200:
        if response:
            assert m_db_get_tempo.call_count == 1
            assert m_db_set_tempo.call_count == 1
            assert m_db_set_tempo_config.call_count == 2

            assert (
                    "ERROR    root:query_tempo.py:78 {'error': True, 'description': 'Erreur lors "
                    "de la récupération de données Tempo.'}\n"
                    not in caplog.text
            )
        else:
            assert m_db_get_tempo.call_count == 1
            assert m_db_set_tempo.call_count == 0
            assert m_db_set_tempo_config.call_count == 0

            assert (
                    "ERROR    root:query_tempo.py:78 {'error': True, 'description': 'Erreur lors "
                    "de la récupération de données Tempo.'}\n" in caplog.text
            )
