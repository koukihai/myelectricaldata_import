from datetime import datetime
from json import JSONDecodeError
from dateutil.relativedelta import relativedelta
import pytest


@pytest.mark.parametrize("response, status_code", [(None, 200), (None, 500), ({"mock": "response"}, 200), ({"2099-01-01": "turquoise"}, 200)])
def test_fetch_tempo(mocker, caplog, requests_mock, response, status_code):
    from models.ajax import Ajax
    from config import URL
    from dependencies import get_version
    start = (datetime.now() - relativedelta(years=3)).strftime("%Y-%m-%d")
    end = (datetime.now() + relativedelta(days=2)).strftime("%Y-%m-%d")

    m_db_get_tempo = mocker.patch("models.datasources.database.Database.get_tempo")
    m_db_set_tempo_config = mocker.patch("models.datasources.database.Database.set_tempo_config")
    m_db_set_tempo = mocker.patch("models.datasources.database.Database.set_tempo")

    requests_mock.get(f"{URL}/rte/tempo/{start}/{end}", json=response, status_code=status_code)
    requests_mock.get(f"{URL}/edf/tempo/days", json=response, status_code=status_code)
    requests_mock.get(f"{URL}/edf/tempo/price", json=response, status_code=status_code)

    ajax = Ajax()

    # FIXME: In case the status_code is not 200 and the response is not a valid json, an exception is raised
    if status_code != 200 and not response:
        with pytest.raises(JSONDecodeError):
            ajax.fetch_tempo()
    else:
        res = ajax.fetch_tempo()
        if status_code == 200 and response and response.get("2099-01-01"):
            assert res == response

            assert m_db_get_tempo.call_count == 1
            assert m_db_set_tempo.call_count == 1
            assert m_db_set_tempo_config.call_count == 0

            assert (
                    "ERROR    root:query_tempo.py:78 {'error': True, 'description': 'Erreur lors "
                    "de la récupération de données Tempo.'}\n"
                    not in caplog.text
            )
        else:
            assert res == "OK"

            assert m_db_get_tempo.call_count == 1
            assert m_db_set_tempo.call_count == 0
            assert m_db_set_tempo_config.call_count == 0

            assert (
                    "ERROR    root:query_tempo.py:78 {'error': True, 'description': 'Erreur lors "
                    "de la récupération de données Tempo.'}\n"
                    in caplog.text
            )