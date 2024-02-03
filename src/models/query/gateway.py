from models.datasources.gatewayapi import GatewayAPI


class Gateway:
    @staticmethod
    def status():
        return GatewayAPI.get_status()
