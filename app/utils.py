import datetime
import logging
import os
from math import floor
from os import environ, getenv, path

from art import decor, text2art

APPLICATION_PATH = environ.get("APPLICATION_PATH", "/app")
APPLICATION_PATH_DATA = getenv("APPLICATION_PATH_DATA", "/data")
CONFIG_PATH = path.join(APPLICATION_PATH_DATA, "config.yaml")

paypal_footer = """
<div style="text-align: center" id="paypal" class="paypal_link">
    <form action="https://www.paypal.com/donate" method="post" target="_top" style="height: 55px;" id="paypal_form">
        <input type="hidden" name="business" value="FY25JLXDYLXAJ" />
        <input type="hidden" name="no_recurring" value="0" />
        <input type="hidden" name="currency_code" value="EUR" />
        <input type="image" id="paypal_img"
               src="/static/img/paypal.png"
               border="0"
               name="submit"
               title="PayPal - The safer, easier way to pay online!"
               alt="Bouton Faites un don avec PayPal"/>
        <img alt="" border="0" src="https://www.paypal.com/fr_FR/i/scr/pixel.gif" width="1" height="1" />
    </form>
    Le service est gratuit, mais si tu souhaites soutenir le projet (serveur & domaine).
</div>
"""


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)


def str2bool(v):
    if not isinstance(v, bool):
        return v.lower() in ("yes", "true", "t", "1")
    return v


def is_float(element):
    try:
        float(element)
        return True
    except ValueError:
        return False


def reformat_json(yaml):
    result = {}
    for key, value in yaml.items():
        if value in ["true", "false"]:
            result[key] = str2bool(value)
        elif type(value) == dict:
            result[key] = value
        elif not isinstance(value, bool) and is_float(value):
            result[key] = float(value)
        else:
            result[key] = value
    return result


def truncate(f, n):
    return floor(f * 10 ** n) / 10 ** n


def title(message):
    separator()
    if type(message) is list:
        for msg in message:
            logging.info(f"{msg.upper()}")
    else:
        logging.info(f"{message.upper()}")
    separator()


def title_warning(message):
    separator_warning()
    logging.warning(f" {message.upper()}")
    separator_warning()


def separator():
    logging.info(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ◦ ❖ ◦ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


def separator_warning():
    logging.warning(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ▲ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


def export_finish():
    logging.info(
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ◦ TERMINE ◦ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


def logo(version):
    Art = text2art("MyElectricalData")
    separator()
    for line in Art.splitlines():
        logging.info(f'{decor("barcode1")}{line: ^93}{decor("barcode1", reverse=True)}')
    separator()
    version = f"VERSION : {version}"
    logging.info(f'{decor("barcode1")}{version: ^93}{decor("barcode1", reverse=True)}')
    separator()


def log_usage_point_id(self, usage_point_id):
    text = f"Point de livraison : {usage_point_id}"
    separator()
    logging.info(f'{decor("barcode1")}{text: ^93}{decor("barcode1", reverse=True)}')
    separator()


def finish():
    finish = text2art("Import Finish!!!")
    separator()
    for line in finish.splitlines():
        logging.info(f'{decor("barcode1")}{line: ^93}{decor("barcode1", reverse=True)}')
    separator()


def get_version():
    with open(os.path.join(APPLICATION_PATH, "VERSION")) as f:
        version = f.read()
    return version.strip()


def log_usage_point_id(usage_point_id):
    text = f"Point de livraison : {usage_point_id}"
    separator()
    logging.info(f'{decor("barcode1")}{text: ^93}{decor("barcode1", reverse=True)}')
    separator()
