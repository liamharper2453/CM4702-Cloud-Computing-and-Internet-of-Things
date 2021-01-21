import asyncio
import io
import threading
import paho.mqtt.client as mqtt
import time
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from PIL import Image

host = "192.168.1.164"
port = 1883
clean_session = True
client_id = "winClient"
colourTopic = "winToPi/colourRequest/winClient"
imageTopic = "winToPi/imageRequest/winClient"
temperatureTopic = "winToPi/temperatureRequest/winClient"
message = ""
responseTopic = "winToPi/response/piClient"
screen_lock = threading.Semaphore(value=1)


def on_connect(client, userdata, flags, rc):
    print("Connect {} result is: {}".format(host, rc))
    if rc == 0:
        client.connected_flag = True
    print("connected ok")
    print("Subscribing to topic: {}".format(responseTopic))
    client.subscribe(responseTopic)
    return

    print("Failed to connect {}, error was, rc={}".format(host, rc))


def on_message(client, userdata, msg):
    screen_lock.acquire()
    print("Topic: {} Message: {}".format(responseTopic, msg.payload.decode()))
    screen_lock.release()


def send_message(client, msg, topic):
    ret = client.publish(topic, msg)
    print("Publish result: {}".format(ret.rc))


async def process_input(client):
    screen_lock.acquire()
    print('Please select one of these options: \n\n'
          '1) Colour\n\n'
          '2) Image\n\n'
          '3) Temperature\n\n')
    screen_lock.release()
    x = input()
    if x == '1':
        screen_lock.acquire()
        print('\n\nEnter a colour:\n\n')
        screen_lock.release()
        x = input()
        send_message(client, x, colourTopic)
    if x == '2':
        Tk().withdraw()
        filename = askopenfilename()
        im = Image.open(filename)
        im = im.resize((8, 8))
        img_byte_arr = io.BytesIO()
        im.save(img_byte_arr, format='PNG')
        x = img_byte_arr.getvalue()
        send_message(client, x, imageTopic)
    if x == '3':
        send_message(client, x, temperatureTopic)
    time.sleep(0.5)


def init_client(client):
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(host, port, keepalive=60)
    client.connected_flag = False
    while not client.connected_flag:
        client.loop()
    client.loop_forever()


async def run():
    client = mqtt.Client(client_id=client_id, clean_session=clean_session)
    thread = threading.Thread(target=init_client, args=(client,))
    thread.daemon = True
    thread.start()
    time.sleep(1)
    while True:
        await process_input(client)


if __name__ == "__main__":
    asyncio.run(run())
