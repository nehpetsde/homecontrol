import paho.mqtt.client as mqtt
from datetime import datetime
from eq3bt import Thermostat
import logging
import time


def mqtt_on_connect(client, userdata, flags, rc):
    logging.info("connected with mqtt server")


thermostat = {
    'bad1': Thermostat('00:1A:22:08:05:20'),
    'bad2': Thermostat('00:1A:22:08:05:39'),
    'leon': Thermostat('00:1A:22:0d:0d:92'),
    'dach': Thermostat('00:1A:22:10:81:6B'),
    'wohn': Thermostat('00:1A:22:10:84:0E'),
}


def set_target_temperature(client, thermostat, message):
    logging.info("%s %s", message.topic, message.payload)
    name = message.topic.split('/')[1]
    temp = float(message.payload)
    try:
        logging.info("set target temperature for '%s' to %.1f", name, temp)
        thermostat[name].target_temperature = temp
        client.publish("thermostat/" + name + "/temperature",
                       str(thermostat[name].target_temperature))
    except Exception:
        logging.error("failed to set target temperatur for '%s'", name)
        client.publish("thermostat/" + name + "/temperature", str(0.0))        


def main():
    client = mqtt.Client(userdata=thermostat)
    client.on_connect = mqtt_on_connect
    client.connect("localhost", 1883, 60)
    client.loop_start()

    for name in thermostat:
        topic = "thermostat/{}/".format(name)
        client.subscribe(topic + "#")
        client.message_callback_add(topic + "target", set_target_temperature)

    adaio = mqtt.Client()
    adaio.username_pw_set("nehpetsde", "806f3bd07f5341deb1ef62a9a995ea5c")
    adaio.connect("io.adafruit.com")

    while True:
        for name in thermostat:
            try:
                thermostat[name].update()
            except Exception:
                logging.error("failed to update '{}'".format(name))
            else:
                client.publish("thermostat/%s/temperature" % name,
                               str(thermostat[name].target_temperature))
                client.publish("thermostat/%s/valve_state" % name,
                               str(thermostat[name].valve_state))
                client.publish("thermostat/%s/low_battery" % name,
                               str(thermostat[name].low_battery))
                adaio.publish("nehpetsde/feeds/thermostat-%s-temp" % name,
                               str(thermostat[name].target_temperature))
                adaio.publish("nehpetsde/feeds/thermostat-%s-valve" % name,
                               str(thermostat[name].valve_state))
            time.sleep(10)
        try:
            adaio.reconnect()
        except Exception:
            logging.error("failed to reconnect io.adafruit.com")
    

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
    try:
        main()
    except KeyboardInterrupt:
        pass
