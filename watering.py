import paho.mqtt.client as mqtt
import requests
import datetime
import logging
import sched
import time


mqtt_broker = 'homecontrol.fritz.box'
device_addr = 'EC:FA:BC:8A:43:D9'  #'DC:4F:22:0E:1F:EF'
device_status = 'dev/wifi/' + device_addr + '/status'
device_switch = 'dev/wifi/' + device_addr + '/switch'


logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)


def mqtt_on_connect(mqtt_client, userdata, flags, rc):
    logging.debug("mqtt connect result %s", mqtt.connack_string(rc))
    mqtt_client.subscribe('home/outdoor/water/switch')
    mqtt_client.subscribe(device_status)


def mqtt_on_message(mqtt_client, scheduler, msg):
    #print(msg.topic, msg.payload)
    if msg.topic == device_status:
        mqtt_client.publish('home/outdoor/water/status', msg.payload)
    elif msg.topic == 'home/outdoor/water/switch':
        minutes = max(0, int(msg.payload))
        if minutes == 0:
            logging.info("Close outdoor water valve.")
            mqtt_client.publish(device_switch, '0')
        else:
            logging.info("Open outdoor water valve for %d minutes.", minutes)
            mqtt_client.publish(device_switch, '1')
            scheduler.enter(minutes * 60, 1, mqtt_client.publish,
                            ('home/outdoor/water/switch', '0'))

def main():
    scheduler = sched.scheduler()
    mqtt_client = mqtt.Client(userdata=scheduler)
    mqtt_client.on_connect = mqtt_on_connect
    mqtt_client.on_message = mqtt_on_message
    mqtt_client.connect(mqtt_broker, 1883, 60)
    mqtt_client.publish(device_switch, '0')
    mqtt_client.loop_start()

    while True:
        if not scheduler.run():
            time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
