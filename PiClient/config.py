# AWS Keys and Certificates
PRIVATE_KEY = "certificates/807ba8c39a-private-pem.key"
DEVICE_CERTIFICATE = "certificates/807ba8c39a-certificate-pem.crt"
ROOT_CERTIFICATE = "certificates/root.crt"

# AWS IoT specific settings
HOST_NAME = "ax90d8h229c69-ats.iot.eu-west-1.amazonaws.com"
HOST_PORT = 8883

# MQTT specific settings
TOPIC = "server_room/metrics/Temperature"
LIGHT_TOPIC_ON = "server_room/temperature_tracking/on"
LIGHT_TOPIC_OFF = "server_room/temperature_tracking/off"

QUALITY_OF_SERVICE_LEVEL = 0
