import ast
from datetime import datetime
from json import JSONDecodeError
from dateutil.relativedelta import relativedelta
import pytest

from db_schema import Ecowatt


@pytest.mark.parametrize("response, status_code", [(None, 200), (None, 500), ({"2099-01-01": {"value": 9000, "message": "mock message", "detail": "mock detail"}}, 200)])
def test_fetch_ecowatt(mocker, caplog, requests_mock, response, status_code):
    from models.ajax import Ajax
    from config import URL

    start = (datetime.now() - relativedelta(years=3)).strftime("%Y-%m-%d")
    end = (datetime.now() + relativedelta(days=3)).strftime("%Y-%m-%d")

    m_db_get_ecowatt = mocker.patch("models.datasources.database.Database.get_ecowatt")
    m_db_set_ecowatt = mocker.patch("models.datasources.database.Database.set_ecowatt")

    m_db_get_ecowatt.return_value = []
    requests_mock.get(f"{URL}/rte/ecowatt/{start}/{end}", json=response, status_code=status_code)

    ajax = Ajax()

    # FIXME: In case the status_code is not 200 and the response is not a valid json, an exception is raised
    if status_code != 200 and not response:
        with pytest.raises(JSONDecodeError):
            ajax.fetch_ecowatt()
    else:
        res = ajax.fetch_ecowatt()
        if status_code == 200 and response and response.get("2099-01-01"):
            assert res == response

            assert m_db_get_ecowatt.call_count == 1
            assert m_db_set_ecowatt.call_count == 1

            assert (
                   "ERROR    root:ecowatt.py:58 {'error': True, 'description': 'Erreur "
                   "lors de la récupération des données Ecowatt.'}\n"
                   not in caplog.text
            )
        else:
            assert res == "OK"

            assert m_db_get_ecowatt.call_count == 1
            assert m_db_set_ecowatt.call_count == 0

            assert (
                    "ERROR    root:ecowatt.py:58 {'error': True, 'description': 'Erreur "
                    "lors de la récupération des données Ecowatt.'}\n"
                    in caplog.text
            )


@pytest.mark.parametrize("response", [None, [Ecowatt(date="2099-01-01", value=9000, message="mock message", detail="{'detail': 'mock detail'}")]])
def test_get_ecowatt(mocker, caplog, response):
    from models.ajax import Ajax

    m_db_get_ecowatt = mocker.patch("models.datasources.database.Database.get_ecowatt")
    m_db_get_ecowatt.return_value = response
    m_db_set_ecowatt = mocker.patch("models.datasources.database.Database.set_ecowatt")

    ajax = Ajax()

    # FIXME: In case the status_code is not 200 and the response is not a valid json, an exception is raised
    if not response:
        with pytest.raises(TypeError):
            ajax.get_ecowatt()
    else:
        res = ajax.get_ecowatt()
        assert res == {r.date: {"value": r.value, "message": r.message, "detail": ast.literal_eval(r.detail)} for r in response}

        assert m_db_get_ecowatt.call_count == 1
        assert m_db_set_ecowatt.call_count == 0

        assert (
                "ERROR    root:ecowatt.py:58 {'error': True, 'description': 'Erreur lors "
                "de la récupération de données Tempo.'}\n"
                not in caplog.text
        )
