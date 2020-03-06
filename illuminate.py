import paho.mqtt.client as mqtt
import datetime
from astral import LocationInfo
from astral.sun import sun
from time import sleep


def main(device, off='23:59'):
    city = LocationInfo('Stuttgart', 'Germany', 'Europe/Berlin')

    mqtt_client = mqtt.Client()
    mqtt_client.connect("localhost", 1883, 60)
    mqtt_client.loop_start()
    mqtt_client.publish(device, "0")

    off = datetime.datetime.strptime(off, '%H:%M').time()

    while True:
        sunset = sun(city.observer)['dusk']

        finish = sunset.replace(hour=off.hour, minute=off.minute)
        if finish < sunset:
            finish += datetime.timedelta(days=1)

        if finish.date() > sunset.date():
            reboot = finish + datetime.timedelta(hours=1)
        else:
            reboot = finish.replace(hour=1) + datetime.timedelta(days=1)

        now = datetime.datetime.now()

        if now < sunset:
            print("illumination starts at", sunset)
            sleep((sunset - now).total_seconds())

        for _ in range(3):
            mqtt_client.publish(device, "1")
            sleep(10)

        now = datetime.datetime.now()

        if now < finish:
            print("illumination finish at", finish)
            sleep((finish - now).total_seconds())

        for _ in range(3):
            mqtt_client.publish(device, "0")
            sleep(10)

        now = datetime.datetime.now()

        if now < reboot:
            print("request next sunset at", reboot)
            sleep((reboot - now).total_seconds())

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('switch')
    parser.add_argument('--finish', default='23:59')
    args = parser.parse_args()
    try:
        print(args)
    except KeyboardInterrupt:
        pass
