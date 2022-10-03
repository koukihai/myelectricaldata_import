from paho.mqtt import client as mqtt

from models.log import critical, log, logSep
from models.config import CONFIG


class Mqtt:

    def __init__(
            self,
            hostname,
            username,
            password,
            client_id="myelectricaldata",
            prefix="myelectricaldata",
            retain=True,
            qos=0,
            port=1883
    ):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.client_id = client_id
        self.prefix = prefix
        self.retain = retain
        self.qos = qos

        self.client = {}
        self.connect()

    def connect(self):
        logSep()
        log(f"Connect to MQTT broker {self.hostname}:{self.port}")
        try:
            self.client = mqtt.Client(self.client_id)
            if self.username != "" and self.password != "":
                self.client.username_pw_set(self.username, self.password)
            self.client.connect(self.hostname, self.port)
            self.client.loop_start()
            log(" => Connected to MQTT Broker!")
        except Exception as e:
            critical(["MQTT Connexion failed", e])

    # def publish(self, client, topic, msg, prefix=None):
    #     if prefix == None:
    #         prefix = main.config["mqtt"]['prefix']
    #     msg_count = 0
    #     result = client.publish(f'{prefix}/{topic}', str(msg), qos=main.config["mqtt"]["qos"],
    #                             retain=main.config["mqtt"]["retain"])
    #     status = result[0]
    #     if status == 0:
    #         log(f" MQTT Send : {prefix}/{topic} => {msg}", "debug")
    #     else:
    #         log(f" - Failed to send message to topic {prefix}/{topic}")
    #     msg_count += 1
    #
    # def subscribe(self, client, topic, prefix=None):
    #     if prefix == None:
    #         prefix = main.config["mqtt"]['prefix']
    #
    #     def on_message(client, userdata, msg):
    #         print(f" MQTT Received : `{prefix}/{topic}` => `{msg.payload.decode()}`")
    #
    #     sub_topic = f"{prefix}/{topic}"
    #     client.subscribe(client, sub_topic)
    #     client.on_message = on_message
