from paho.mqtt import client as mqtt
from sense_hat import SenseHat
from phue import Bridge
from matplotlib import colors
from rgbxy import Converter
from rgbxy import GamutA
from PIL import Image
import io
import time

host='192.168.1.164'
port = 1883
client_id='piClient'
colour_topic = "winToPi/colourRequest/winClient"
image_topic = "winToPi/imageRequest/winClient"
temperature_topic = "winToPi/temperatureRequest/winClient"
response_topic = "winToPi/response/piClient"
sense = SenseHat()
bridge = Bridge('192.168.1.134')
converter = Converter(GamutA)

def on_connect(client, userdata, flags, rc):
         if rc == 0:
                 print("Connected to MQTT server.")
                 print("Subscribing to topic: {}".format(colour_topic))
                 print("Subscribing to topic: {}".format(image_topic))
                 print("Subscribing to topic: {}".format(temperature_topic))
                 client.subscribe(colour_topic)
                 client.subscribe(image_topic)
                 client.subscribe(temperature_topic)
                 initialise_hue()
         else:
                print("Failed to connect, return code {}".format(rc))

def on_message(client, userdata, msg):
        
            print("Topic: {} Message: {}".format(msg.topic,'image'))
            if(msg.topic == colour_topic):
                print("Topic: {} Message: {}".format(msg.topic,msg.payload.decode()))
                rgb_colour = set_colour_on_hue(client, msg.payload.decode())
                if (rgb_colour is not None):
                    update_sense_hat_display(msg.payload.decode(), rgb_colour)
            
            if(msg.topic == image_topic):  
                image = Image.open(io.BytesIO(msg.payload))
                image.show()
                print(image.format)
                image.save('/home/pi/test.png')
                update_sense_hat_display_with_image('/home/pi/test.png')
            
            if(msg.topic == temperature_topic):
                maxTemp = 46;
                minTemp = 38;
                while True:
                    temp = sense.get_temperature()
                    redVal = 255 / (maxTemp - minTemp) * (temp - minTemp);
                    blueVal = 255 / (maxTemp - minTemp) * (maxTemp - temp);
                    rgb_colour = set_colour_on_hue(client, '', (redVal / 255, 0, blueVal / 255))
                    if (rgb_colour is not None):
                        update_sense_hat_display_with_temp(rgb_colour)

                    time.sleep(1)
            
            
def initialise_hue():
        return
        #bridge.connect()
        #bridge.get_api()
    
def set_colour_on_hue(client, msg, rgb = ''):
        try:
            rgb_colour = colors.to_rgb(msg.replace(' ', '')) if rgb == '' else rgb
            print(sense.get_temperature())
            xy_colour = converter.rgb_to_xy(rgb_colour[0], rgb_colour[1],rgb_colour[2])
            if (xy_colour is None):
                raise Exception
            #lights = bridge.get_light_objects('list')
            #for light in lights:
                #light.on = True
                #light.xy = xy_colour
                #light.brightness = 255
            lights = bridge.get_light_objects('name')
            desk_light = lights["Desk Light"]
            desk_light.on = True
            desk_light.xy = xy_colour
            desk_light.brightness = 255
            client.publish(response_topic, "Colour set to "
                           + msg)
        except:
            client.publish(response_topic, msg
                           + " is not a valid colour")
            return
        return rgb_colour
                       
def update_sense_hat_display(msg, rgb_colour):
        sense.show_message(msg, text_colour=[int(rgb_colour[0] * 255), int(rgb_colour[1] * 255),int(rgb_colour[2] * 255)])
        sense.show_message('', back_colour=[int(rgb_colour[0] * 255), int(rgb_colour[1] * 255),int(rgb_colour[2] * 255)])
        
def update_sense_hat_display_with_temp(rgb_colour):
        sense.show_message('', back_colour=[int(rgb_colour[0] * 255), int(rgb_colour[1] * 255),int(rgb_colour[2] * 255)])


def update_sense_hat_display_with_image(msg):
        sense.load_image(msg)
        
def run():
         client=mqtt.Client(client_id=client_id)
         client.on_connect=on_connect
         client.on_message=on_message
         client.connect(host,port)
         client.loop_forever()       
         
if __name__ == '__main__':
 run()