import paho.mqtt.client
import datetime
import requests
import logging
import parsel
import redis


# Get the water balance (precipitation - evaporation) for the past N days
def get_water_balance(N=1):
    url = "https://dlr-web-daten1.aspdienste.de/cgi-bin/wetter.dd.pl"
    sel = '//td[contains(@style,"background-color:#EEFFFF")]//text()'
    Y, M, D = datetime.date.today().timetuple()[:3]
    result = list()
    if D < N + 1:
        r = requests.get(url, {'c': 2, 'sid': 94, 'y': Y, 'm': M-1, 't': 50})
        result.extend(parsel.Selector(r.text).xpath(sel).getall()[:-4])
    r = requests.get(url, {'c': 2, 'sid': 94, 'y': Y, 'm': M, 't': 50})
    result.extend(parsel.Selector(r.text).xpath(sel).getall()[:-4])
    return sum((float(val) for val in result[-N:]))


def get_rainfall_sum(date=None):
    url = "https://dlr-web-daten1.aspdienste.de/cgi-bin/wetter.hh.pl"
    sel = '//td[contains(@style,"background-color:#EEFFFF")]//text()'
    Y, M, D = (datetime.date.today() if date is None else date).timetuple()[:3]
    r = requests.get(url, {'c': 2, 'sid': 94, 'y': Y, 'm': M, 'd': D, 't': 11})
    return float(parsel.Selector(r.text).xpath(sel).getall()[-1])


# Get the water dispense event for the past N days from the Redis database
def get_water_dispense(rddb, N=1):
    today = datetime.datetime.combine(datetime.date.today(), datetime.time())
    start = int((today - datetime.timedelta(days=N)).timestamp() * 1000)
    events = rddb.xrange("water.valve.1", start)
    return sum(int(D.get(b"dispense", 0)) for T, D in events)


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

    rddb = redis.Redis("homecontrol")
    mqtt = paho.mqtt.client.Client()
    
    days = 5
    balance = get_water_balance(days) + get_water_dispense(rddb, days) / 2
    logging.info(f"Current water balance: {balance:.1f} ltr")
    if balance < 0:
        if mqtt.connect("homecontrol") == paho.mqtt.client.MQTT_ERR_SUCCESS:
            mqtt.publish("home/outdoor/water/switch", 30)
            rddb.xadd("water.valve.1", {"dispense": 30})
        else:
            logging.warning("MQTT connection error")

