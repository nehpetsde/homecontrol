from fritzconnection import FritzConnection
import paho.mqtt.client as mqtt
from datetime import datetime
from shutil import copyfile
from time import sleep
import os


def get_bytes_rcvd(fc):
    try:
        r = fc.call_action("WANCommonInterfaceConfig", "GetTotalBytesReceived")
        return r.get("NewTotalBytesReceived", 0)
    except Exception:
        return 0


def get_bytes_sent(fc):
    try:
        r = fc.call_action("WANCommonInterfaceConfig", "GetTotalBytesSent")
        return r.get("NewTotalBytesSent", 0)
    except Exception:
        return 0


def get_host_count(fc):
    try:
        r = fc.call_action('Hosts', 'GetHostNumberOfEntries')
        return r.get('NewHostNumberOfEntries', 0)
    except Exception:
        return 0


def get_host_entry(fc, index):
    try:
        return fc.call_action('Hosts', 'GetGenericHostEntry', NewIndex=index)
    except Exception:
        return {}


def mqtt_on_connect(client, userdata, flags, rc):
    print("connected with mqtt server")
    pass


def main():
    fritz_user = os.environ['FRITZ_USER']
    fritz_pass = os.environ['FRITZ_PASS']

    logdir = os.path.join(os.environ.get('HOME'), "homecontrol.log/fritzbox")

    if not os.path.isdir(logdir):
        os.makedirs(logdir)

    client = mqtt.Client()
    client.on_connect = mqtt_on_connect
    client.connect("localhost", 1883, 60)
    client.loop_start()

    fc = FritzConnection(user=fritz_user, password=fritz_pass)
    print("connected with fritz box")

    sleep_time = 60  # seconds
    copy_delay = 60  # x sleep_time
    copy_count = 0

    while True:
        now = datetime.now()
        log_date = now.date().strftime('%Y%m%d')
        log_time = now.time().strftime('%H:%M:%S')

        bytes_rcvd = get_bytes_rcvd(fc)
        bytes_sent = get_bytes_sent(fc)

        devices_by_addr = []
        devices_by_name = []
        for host_index in range(get_host_count(fc)):
            host_entry = get_host_entry(fc, host_index)
            #print(host_index, host_entry)
            is_wlan = host_entry.get('NewInterfaceType') == '802.11'
            is_dhcp = host_entry.get('NewAddressSource') == 'DHCP'
            is_active = host_entry.get('NewActive') is True
            if is_wlan and is_dhcp and is_active:
                devices_by_addr.append(host_entry.get('NewMACAddress'))
                devices_by_name.append(host_entry.get('NewHostName'))

        with open("/tmp/devaddr-{}.log".format(log_date), 'a') as logfile:
            print(log_time, ' '.join(devices_by_addr), file=logfile)

        with open("/tmp/devname-{}.log".format(log_date), 'a') as logfile:
            print(log_time, ' '.join(devices_by_name), file=logfile)

        with open("/tmp/traffic-{}.log".format(log_date), 'a') as logfile:
            print(log_time, bytes_sent, bytes_rcvd, file=logfile)

        client.publish("fritzbox/status/sent/b", str(bytes_sent))
        client.publish("fritzbox/status/rcvd/b", str(bytes_rcvd))
        client.publish("fritzbox/status/sent/kb", str(int(bytes_sent // 2**10)))
        client.publish("fritzbox/status/rcvd/kb", str(int(bytes_rcvd // 2**10)))
        client.publish("fritzbox/status/sent/mb", str(int(bytes_sent // 2**20)))
        client.publish("fritzbox/status/rcvd/mb", str(int(bytes_rcvd // 2**20)))

        athome = (v for v in devices_by_name if v.startswith("Smartphone-"))
        client.publish('athome', ' '.join(v.split('-')[1] for v in athome))

        if copy_count == 0 and os.path.isdir(logdir):
            for entry in os.scandir('/tmp'):
                for logtype in ['traffic-', 'devname-', 'devaddr-']:
                    if entry.name.startswith(logtype):
                        srcname = os.path.join('/tmp', entry.name)
                        dstname = os.path.join(logdir, entry.name) 
                        print('saving {} to {}'.format(srcname, dstname))
                        copyfile(srcname, dstname)
                        if not entry.name.startswith(logtype + log_date):
                            os.remove(srcname)

        copy_count = (copy_count + 1) % copy_delay
        sleep(sleep_time)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
