# Disable ds2490 module #

```
sudo sh -c "echo ds2490 >> /etc/modprobe.d/blacklist"
```

# Add hotplug permissions #

/etc/udev/rules.d/40-basic-permissions.rules
```
SUBSYSTEM=="usb", ENV{DEVTYPE}=="usb_device",SYSFS{idVendor}=="04fa" , SYSFS{idProduct}=="2490", MODE="0666"
```