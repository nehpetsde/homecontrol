# homecontrol

/etc/rc.local
```
tvservice -o
echo 0 > /sys/devices/platform/soc/3f980000.usb/buspower
su --login --command "homecontrol/startup.sh" pi
exit 0
```
