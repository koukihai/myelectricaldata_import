## Contributing

### Running unittests
1. Start homeassistant and MQTT
```commandline
docker compose -f docker-compose.unittests.yaml --remove-orphans
```
2. Run unittests

### Running integration tests
1. Start homeassistant, mqtt and myelectricaldata
```commandline
docker compose -f docker-compose.yaml --build myelectricaldata
```