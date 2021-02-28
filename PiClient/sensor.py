# Simple application that periodically collects sensor data from a Raspberry Pi SenseHat and sends the data to the
# AWS MQTT broker with the AWS MQTT client API
# Code to get adjusted CPU temperature taken from https://yaab-arduino.blogspot.com/2016/08/accurate-temperature-reading-sensehat.html

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from sense_hat import SenseHat
from matplotlib import colors
from rgbxy import Converter
from rgbxy import GamutA
from phue import Bridge
import config
import time
import json
import threading
import math
import os
from datetime import datetime, timedelta

sense = SenseHat()
bridge = Bridge('192.168.1.134')
converter = Converter(GamutA)
sense.clear()

# Define variable for MQTT topic from config file
sensor_topic = config.TOPIC

# Initialize MQTT client
client = AWSIoTMQTTClient('')
bridge.run_scene('Bedroom', 'Dimmed')
sense.clear()

# Configure MQTT client
client.configureEndpoint(config.HOST_NAME, config.HOST_PORT)
client.configureCredentials(config.ROOT_CERTIFICATE, config.PRIVATE_KEY, config.DEVICE_CERTIFICATE)
client.configureOfflinePublishQueueing(-1)
client.configureDrainingFrequency(2)
client.configureConnectDisconnectTimeout(10)
client.configureMQTTOperationTimeout(5)


# Retrieves and constructs temperature data payload
def get_temperature(id):
    temperature = float(get_derived_temperature())
    rgb = get_rgb_from_temperature(temperature)
    rgb_to_return = [int(rgb[0] * 255), int(rgb[1] * 255),int(rgb[2] * 255)]
    timestamp = str(datetime.now())
    ttl = datetime.now() + timedelta(hours=1)
    payload = {'ID': id, 'Temperature': temperature, 'RGB': rgb_to_return, 'Timestamp': timestamp, 'TTL': int(ttl.strftime("%s"))}
    return payload

# Creates background thread responsible for setting temperature values on the Phillips Hue light and SenseHAT
def light_topic_on(client, userdata, msg):
        print('Now displaying temperature to SenseHat and Hue light')
        thread = threading.Thread(target=set_light_and_sense_hat, args=(client,userdata,msg,))
        thread.daemon = True
        thread.start()

# Sets Phillips Hue light and SenseHAT LCD display back to defaults
def light_topic_off(client, userdata, msg):
        print('Now disabling the display of temperature to SenseHat and Hue light')
        bridge.run_scene('Bedroom', 'Dimmed')
        sense.clear()

# Sets temperature values on the Phillips Hue light and SenseHAT
def set_light_and_sense_hat(client,userdata,msg):
    t_corr = float(msg.payload.decode())
    rgb_colour = get_rgb_from_temperature(t_corr)
    # If temperature over 39 degrees then flash red on Phillips Hue light instead of using RGB converted value
    if (t_corr >= 39):
        critical_temperature_warning_on_hue()
    else:
        set_colour_on_hue(rgb_colour)
    if (rgb_colour is not None):
        update_sense_hat_display_with_temp(rgb_colour, t_corr)
    

# Flash red on Phillips Hue light
def critical_temperature_warning_on_hue():
     try:
            xy_colour = converter.rgb_to_xy(255, 0, 0)
            if (xy_colour is None):
                raise Exception
            lights = bridge.get_light_objects('name')
            desk_light = lights["Desk Light"]
            desk_light.on = True
            desk_light.xy = xy_colour
            desk_light.brightness = 255
            time.sleep(0.5)
            desk_light.brightness = 0
     except:
            print('Phillips Hue light could not be set')
            return
     return

# Derives RGB values from numerical temperature value based on temperature ranges
def get_rgb_from_temperature(temperature):
    max_temp = 40;
    min_temp = 28;
    red_val = 255 / (max_temp - min_temp) * (temperature - min_temp)
    blue_val = 255 / (max_temp - min_temp) * (max_temp - temperature)
    return colors.to_rgb((red_val / 255, 0, blue_val / 255))
    
# Derives adjusted temperture as using SenseHAT readings alone can be inaccurate
# Taken from https://yaab-arduino.blogspot.com/2016/08/accurate-temperature-reading-sensehat.html
def get_derived_temperature():
        temp = sense.get_temperature()
        t1 = sense.get_temperature_from_humidity()
        t2 = sense.get_temperature_from_pressure()
        t_cpu = get_cpu_temp()
        h = sense.get_humidity()
        p = sense.get_pressure()

        t = (t1+t2)/2
        t_corr = t - ((t_cpu-t)/1.5)
        t_corr = get_smooth(t_corr)
        return t_corr
    
# Converts RGB value to XY value for use in Phillips Hue light    
def set_colour_on_hue(rgb_colour = ''):
        try:
            xy_colour = converter.rgb_to_xy(rgb_colour[0], rgb_colour[1],rgb_colour[2])
            if (xy_colour is None):
                print('RGB' + rgb_colour + ' could not be converted to XY value')
                raise Exception
            lights = bridge.get_light_objects('name')
            desk_light = lights["Desk Light"]
            desk_light.on = True
            desk_light.xy = xy_colour
            desk_light.brightness = 255
        except:
            print('Phillips Hue light could not be set')
            return
        return rgb_colour

# Displays numerical temperature value on SenseHAT along with setting background of SenseHAT display using RGB colour
def update_sense_hat_display_with_temp(rgb_colour, t_corr):
        sense.show_message(str(math.floor(t_corr)) + 'C', back_colour=[int(rgb_colour[0] * 255), int(rgb_colour[1] * 255),int(rgb_colour[2] * 255)])

# Get CPU temperature
# Taken from https://yaab-arduino.blogspot.com/2016/08/accurate-temperature-reading-sensehat.html
def get_cpu_temp():
  res = os.popen("vcgencmd measure_temp").readline()
  t = float(res.replace("temp=","").replace("'C\n",""))
  return(t)

# Uses moving average to smooth readings
# Taken from https://yaab-arduino.blogspot.com/2016/08/accurate-temperature-reading-sensehat.html
def get_smooth(x):
  if not hasattr(get_smooth, "t"):
    get_smooth.t = [x,x,x]
  get_smooth.t[2] = get_smooth.t[1]
  get_smooth.t[1] = get_smooth.t[0]
  get_smooth.t[0] = x
  xs = (get_smooth.t[0]+get_smooth.t[1]+get_smooth.t[2])/3
  return(xs)

def main():
# Connect
    print('Connecting to endpoint ' + config.HOST_NAME)
    client.connect()
    print('Subscribing to "' + config.LIGHT_TOPIC_ON + '"')
    client.subscribe(config.LIGHT_TOPIC_ON, 1, light_topic_on)
    print('Subscribing to "' + config.LIGHT_TOPIC_OFF + '"')
    client.subscribe(config.LIGHT_TOPIC_OFF, 1, light_topic_off)
    # Loop and publish temperature data every 3 seconds
    id = 0
    while True:
        data = {key: get_temperature(id)[key] for key in ('Temperature', 'ID', 'RGB', 'Timestamp', 'TTL')}
        sub_topic = sensor_topic.split('/')[0] + '/metrics/' + 'Temperature'
        client.publish(sub_topic, json.dumps(data), config.QUALITY_OF_SERVICE_LEVEL)
        print('The temperature in the server room currently is ' + str(data['Temperature']) + '. Successfully published to '
                                                                                               'topic ' + sub_topic)
        client.publish(sensor_topic, json.dumps(get_temperature(id)), config.QUALITY_OF_SERVICE_LEVEL)
        print('Server room temperature published to topic ' + sensor_topic)
        id += 1
        time.sleep(3)
        
if __name__ == "__main__":
    main()