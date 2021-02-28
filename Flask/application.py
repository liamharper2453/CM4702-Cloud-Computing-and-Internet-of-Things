# application.py
# Web application that retrieves data from an MQTT topic, populates a DynamoDB table with the data,
# and serves a web interface with streaming graphs.
# Work related to graphs taken from https://github.com/aws-samples/aws-iot-office-sensor for the most part

import threading
from time import sleep
from flasgger import Swagger
import config
import boto3
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from utils import *
import json
from flask import Flask, render_template
from bokeh.embed import components

# Initialise configuration variables
region_name = config.REGION_NAME
aws_access_key_id = config.AWS_ACCESS_KEY_ID
aws_secret_access_key = config.AWS_SECRET_ACCESS_KEY
table_name = config.TABLE_NAME
window = config.CALC_WINDOW

# Initialise database client
dynamodb = boto3.client("dynamodb", region_name=region_name, aws_access_key_id=aws_access_key_id,
                        aws_secret_access_key=aws_secret_access_key)

# Initialise data structures
metrics_data = {}
last_recorded_collection = {}

# Set configuration variables
data_topic = config.DATA_TOPIC

# Initialise MQTT client
client = AWSIoTMQTTClient('')

# Configure MQTT client
client.configureEndpoint(config.HOST_NAME, config.HOST_PORT)
client.configureCredentials(config.ROOT_CERTIFICATE, config.PRIVATE_KEY, config.DEVICE_CERTIFICATE)
client.configureOfflinePublishQueueing(-1)
client.configureDrainingFrequency(2)
client.configureConnectDisconnectTimeout(10)
client.configureMQTTOperationTimeout(5)

temperature_tracking_enabled = False


# Define callback to update data when topic defined in configuration has been published to
def callback(client, userdata, message):
    global metrics_data, last_recorded_collection
    metric = str(message.topic.split('/')[2])
    data = history(dynamodb, table_name, metric, json.loads(message.payload.decode())['ID'])
    last_recorded_collection = data.iloc[-1]
    stats = calculate_mas(metric, data, window)
    metrics_data[metric] = stats

# Connect
print('Connecting to endpoint ' + config.HOST_NAME)
client.connect()

# Subscribe to MQTT topic, trigger callback if topic defined in configuration file has been published to
print('Subscribing to "' + data_topic + '"')
client.subscribe(data_topic, 1, callback)

# Initialise Flask application, static folder contains .js and .css files
application = Flask(__name__, static_folder="static")

# Initialise Swagger
application.config['SWAGGER'] = {
    "swagger_version": "2.0",
    "title": "Temperature Tracking",
    "headers": [
        ('Access-Control-Allow-Origin', '*'),
        ('Access-Control-Allow-Methods', "GET, POST, PUT, DELETE, OPTIONS"),
        ('Access-Control-Allow-Credentials', "true"),
    ],
    "specs": [
        {
            "version": "0.0.1",
            "title": "Temperature Tracking Api v1",
            "endpoint": 'v1_spec',
            "description": 'This is version 1 of the Temperature Tracking API',
            "route": '/v1/spec'
        }
    ]
}

swagger = Swagger(application)
x_label = "Time"

# Render HTML web page containing a graph showing moving average over time
def render_metric(metric, unit):
    title = metric + ": Observations and Moving Averages"
    metric_unit = metric + ", " + unit
    plot = plot_data(metrics_data[metric], title, x_label, metric_unit)
    script, div = components(plot)
    data = metrics_data[metric].to_dict()
    return render_template("temperature_tracking.html", metric=metric, data=data, script=script, div=div)

# Every 5 seconds, publish to MQTT to tell Raspberry Pi to update Phillips Hue light and SenseHAT display
def process_temperature_tracking():
    while temperature_tracking_enabled:
        client.publish(config.LIGHT_TOPIC_ON, last_temperature(), config.QUALITY_OF_SERVICE_LEVEL)
        sleep(5)
    temperature_tracking_off()

@application.route('/')
@application.route('/temperature_tracking')
def temperature_tracking():
    """This is the homepage and is used to render the temperature_tracking.html file with graph that shows all recorded observations with an average of temperature over time
         ---
         responses:
           200:
             description: Homepage loaded with graph information loaded but hidden
         """
    return render_metric("Temperature", "C")

@application.route('/temperature_tracking_off')
def temperature_tracking_off():
    """Publishes MQTT message to disable temperature tracking and returns success message
        ---
        definitions:
          Message:
            type: object
            properties:
              msg:
                type: string
        responses:
          200:
            description: Temperature Tracking Off message published successfully
            examples:
             {"msg": "Temperature Tracking Off message published successfully"}
        """
    global temperature_tracking_enabled
    temperature_tracking_enabled = False
    client.publish(config.LIGHT_TOPIC_OFF, '', config.QUALITY_OF_SERVICE_LEVEL)
    return {"msg": "Temperature Tracking Off message published successfully"}, 201

@application.route('/temperature_tracking_on')
def temperature_tracking_on():
    """Publishes MQTT message to enable temperature tracking and returns success message
            ---
            definitions:
              Message:
                type: object
                properties:
                  msg:
                    type: string
            responses:
              200:
                description: Temperature Tracking On message published successfully
                examples:
                 {"msg": "Temperature Tracking On message published successfully"}
            """
    global temperature_tracking_enabled
    temperature_tracking_enabled = True
    thread = threading.Thread(target=process_temperature_tracking, args=())
    thread.daemon = True
    thread.start()
    return {"msg": "Temperature Tracking On message published successfully"}, 201

@application.route('/last_temperature')
def last_temperature():
    """Returns last recorded temperature from the ServerRoomSensor DynamoDb table
      ---
      definitions:
        Last Temperature:
          type: number
      responses:
        200:
          description: Last recorded temperature value received successfully
          examples:
            36.4
      """
    global last_recorded_collection
    return str(last_recorded_collection[0])

@application.route('/last_rgb')
def last_rgb():
    """Returns last recorded RGB value from the ServerRoomSensor DynamoDb table
      ---
      definitions:
        Last RGB:
          type: string
      responses:
        200:
          description: Last recorded RGB value received successfully
          examples:
            [255,0,0]
      """
    global last_recorded_collection
    return str(last_recorded_collection[2][0]['N'] + ',' +
               last_recorded_collection[2][1]['N'] + ',' +
               last_recorded_collection[2][2]['N'])

if __name__ == '__main__':
    application.run(debug=True)