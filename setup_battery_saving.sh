# Disable HDMI, USB-BUS

echo '
[Unit]
Description=Save battery disabling HDMI, USB bus

[Service]
Type=oneshot
ExecStart=/opt/vc/bin/tvservice -o; /bin/sh -c "echo Bus Power = 0x0 > /sys/devices/platform/soc/20980000.usb/buspower"
ExecStop=/opt/vc/bin/tvservice -p; /bin/sh -c "echo Bus Power = 0x1 > /sys/devices/platform/soc/20980000.usb/buspower"
RemainAfterExit=yes

[Install]
WantedBy=default.target
' > ports_off.service

sudo cp ports_off.service /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable ports_off

# Disable LEDS

echo "dtparam=act_led_trigger=none" | sudo tee -a /boot/config.txt
echo "dtparam=act_led_activelow=on" | sudo tee -a /boot/config.txt

# Disable Bluetooth

echo "dtoverlay=pi3-disable-bt" | sudo tee -a /boot/config.txt
sudo systemctl disable hciuart
sudo systemctl disable bluetooth

