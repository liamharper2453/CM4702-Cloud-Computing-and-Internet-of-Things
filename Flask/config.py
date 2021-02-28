# config.py

# AWS IoT endpoint settings
HOST_NAME = "ax90d8h229c69-ats.iot.eu-west-1.amazonaws.com"
HOST_PORT = 8883
PRIVATE_KEY = "certificates/807ba8c39a-private-pem.key"
DEVICE_CERTIFICATE = "certificates/807ba8c39a-certificate-pem.crt"
ROOT_CERTIFICATE = "certificates/root.crt"
REGION_NAME = "eu-west-1"
AWS_ACCESS_KEY_ID = "AKIAJCIMDKUTT64PN4QQ"
AWS_SECRET_ACCESS_KEY = "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"

# DynamoDB settings
TABLE_NAME = "ServerRoomSensor"

# MQTT message settings
DATA_TOPIC = "server_room/metrics/Temperature"
LIGHT_TOPIC_ON = "server_room/temperature_tracking/on"
LIGHT_TOPIC_OFF = "server_room/temperature_tracking/off"
QUALITY_OF_SERVICE_LEVEL = 0

# Data processing settings
CALC_WINDOW = 10