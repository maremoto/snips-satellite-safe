# snips-satellite-safe
SAFE code for satellite pendant, not an SNIPS app.

[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/maremoto/snips-satellite-safe/blob/master/LICENSE)

<img src="https://github.com/maremoto/snips-resources-safe/blob/master/docs/SAFE.png" alt="SAFE logo">

This is the code to deploy in the satellite (pendant) devices of the SAFE solution.

A pendant does not implement a full Snips platform, but only the audio server service, and most of the functionality relays in the [Base platform](https://github.com/maremoto/snips-app-safe/blob/master/README.md).

## Features

This is a system to provide basic assistance to old or somehow impaired people at home, using the dialog features of the snips platform.
The hotword "hey Snips" is disabled.

- Pushing the button in the pendant makes the assistant start a help request and activate voice interface. 
- The assistant will require who to call among the contacts, or if the alarm should be raised.
- If no answer is provided, the alarm will raise automatically and the default contact will be called.

### Intents

- helpMe - start assistance
- callSomeone - do a call to a given contact
- everythingIsOk - stop assistance
- alarm - raise the alarm to alert the neighbors

### Button

Pressing the button will be equivalent to the intent "helpMe".
Furthermore, pushing the button will end a call or to stop de sound alarm.

## Hardware and third party software

The app is developed for Raspberry pi Zero W with sound capabilities configured (microphone and speaker).
For a hardware device creation see the [Hackster project](https://www.hackster.io/maremoto/snips-assistant-for-emergencies-safe-c3c178).

The snips voice platform will be installed in the [Raspberry pi Zero](https://docs.snips.ai/getting-started/quick-start-raspberry-pi), but only the audio service.

The app requires linphone software console [linphonec](https://www.linphone.org/technical-corner/linphone) to be deployed and available in command line. Find detailed instructios at the [resources project](https://github.com/maremoto/snips-resources-safe/blob/master/README.md).

## Installation

### Snips sound service and MQTT protocol

We do not install the entire Snips Voice Platform, but only the Snips Audio Server and Snips Watch component:

```bash
sudo apt-get update
sudo apt-get install -y dirmngr
sudo bash -c 'echo "deb https://raspbian.snips.ai/$(lsb_release -cs) stable main" > /etc/apt/sources.list.d/snips.list'
sudo apt-key adv --keyserver pgp.mit.edu --recv-keys D4F50CDCA10A2849
sudo apt-get update
sudo apt-get install -y snips-audio-server snips-watch
```

Configure users permissions:

```bash
sudo adduser root audio
sudo usermod -a -G gpio,audio _snips
```

### Snips configuration at the pendant (satellite)

The communication with the base is vital for the satellite, so it has to be configured:

```bash
sudo vi /etc/snips.toml

		#at [snips-common]
	mqtt = "192.168.1.50:1883"

		#at [snips-audio-server]
	bind = "safependant0@mqtt"
```

The audio server will be disabled because of energy saving considerations, it will be start when the user pushes the button.

```bash
sudo systemctl stop snips-audio-server
sudo systemctl disable snips-audio-server
```

> ***The configuration assumes that the base ip is 192.168.1.50 in the home wi-fi network***
> ***You may prepare and attach more than one pendant to the same base, just beware of changing the id safependant0 for any other id (e.g. safependant1, safependant2...) throughout the configuration.***

### Snips configuration at the base

For every satellite pendant that you want to deploy, the Snips software at the base will require some configuration:

```bash
sudo vi /etc/snips.toml

		#at [snips-audio-server]
	bind = "safebase@mqtt"

		#at [snips-hotword]
	audio = ["safebase@mqtt", "safependant0@mqtt"]

sudo systemctl restart snips-*
```

If there is more than one pendant, add further elements at the `[snips-hotword]` section in the `audio` list.

### Pendant software

The software deployment begins by cloning this repository, placing the software, and executing setup utility with pi user:

```
git clone https://github.com/maremoto/snips-satellite-safe.git
cp -r snips-satellite-safe /var/lib/snips/snips-satellite-safe
cd snips-satellite-safe
./setup.sh
```

Then create a service to autostart at boot, but let it disabled until the configuration is complete:

```bash
cd snips-satellite-safe
sudo cp snips-safependant-server.service /etc/systemd/system
sudo chmod 755 /etc/systemd/system/snips-safependant-server.service
sudo systemctl daemon-reload
sudo systemctl disable snips-safependant-server
```

### Checking with sam

First run `sam connect` to connect to your raspberry (base or satellite).
Then run `sam status` to get the satellite and base configurations.

The output should be similar to this one:

```bash
pi@snips-base:~/app_home $ sam connect localhost
? Enter username for the device: pi
? Enter password for the device: [hidden]
✔ Connected to localhost
i A public key has been generated and copied to the device at localhost:~/.ssh/authorized_keys 
pi@snips-base:~/app_home $ sam status

Connected to device localhost

OS version ................... Raspbian GNU/Linux 9 (stretch)
Installed assistant .......... SAFE
Language ..................... en
Hotword ...................... hey_snips
ASR engine ................... snips
Status ....................... Live

Service status:

snips-analytics .............. 0.62.3 (not running)
snips-asr .................... 0.62.3 (running)
snips-audio-server ........... 0.62.3 (running)
snips-dialogue ............... 0.62.3 (running)
snips-hotword ................ 0.62.3 (running)
snips-nlu .................... 0.62.3 (running)
snips-skill-server ........... 0.62.3 (running)
snips-tts .................... 0.62.3 (running)
 
pi@snips-base:~/app_home $ sam connect snips-sat
? Enter username for the device: pi
? Enter password for the device: [hidden]
✔ Connected to snips-sat
i A public key has been generated and copied to the device at snips-sat:~/.ssh/authorized_keys 
pi@snips-base:~/app_home $ sam status

Connected to device snips-sat.local

OS version ................... Raspbian GNU/Linux 9 (stretch)
Installed assistant .......... Not installed
Status ....................... Idle (no assistant)

Service status:

snips-analytics .............. (not running)
snips-asr .................... (not running)
snips-audio-server ........... 0.62.3 (not running)
snips-dialogue ............... (not running)
snips-hotword ................ (not running)
snips-nlu .................... (not running)
snips-skill-server ........... (not running)
snips-tts .................... (not running)
```

> ***Check that the hermes version installed in the satellite matches with the one in the base device.***

### System configuration

All the configuration options of the software are written in `config.ini` file at `/var/lib/snips/snips-satellite-safe`. 
There are three sections used to represent three different kinds of parameters. Please refer to your actual usage to modify.
> ***Whenever the configuration is modified, the sevice will need a restart:***
```bash
sudo systemctl restart snips-safependant-server
```

Every pendant may be customized with a different client name and a sos wav message, but the contacts list and the default contact (Emergency) are common to all and configured in the base.

#### `[secret]`

This section contains the user options.

| Config | Description | Default |
| --- | --- | --- |
| `client_name` | Customised name that the voice interface uses to adress the customer. ***Optional*** | ***Empty*** |

> ***The `default_contact` has to exist among the configured contacts (see below)***

#### `[global]`

This section contains some options related to the software and hardware configuration.

| Config | Description | Value | Default |
| --- | --- | --- | --- |
| `mqtt_host` | MQTT server host name | `<ip address>`/`<hostname>` | `192.168.1.50` |
| `mqtt_port` | MQTT port number | `<mqtt port>` | `1883` |
| `site_id` | Snips device ID | Refering to the actual `snips.toml` | `safependant0` |
| `button_gpio_bcm` | Button gpio pin | Depends on the hardware configuration | `11` |
| `led_gpio_bcm` | LEDs gpio pin | Depends on the hardware configuration | `13` |
| `lbo_gpio_bcm` | Relay gpio pin | Depends on the hardware configuration ***FUTURE use*** | `36` |
| `power_saving` | If power saving is activated with the SAFE service | `0=no 1=yes` | `0` |

The gpio options will not change if the hardware device is built as described at the Hackster project.
> ***The `power_saving` parameter should be set to 0 when the device is being tested and deployed, and set to 1 at the end, because it makes the service to turn off wi-fi connection and ssh service*** 

#### `[phone]`

Sofpthone invoke configuration, .

| Config | Description | Default |
| --- | --- | --- |
| `softphone_config_file` | Softphone configuration file name (relative to app path) with linphone formatting | linphonerc.ini |
| `timeout_call_end` | Seconds to wait for a call to end, avoid inconsistent situations | `900` |
| `capture_soundcard_name` | ALSA name of the capture sound card | ***Empty*** |
| `playback_soundcard_name` | ALSA name of the playback sound card | ***Empty*** |
| `sos_message_wav` | Wav file name (relative to app path) to play when a default call is made. ***Optional*** | ***Empty*** |

> ***The `linphonerc.ini` file in the project is only a sample, and has to be modified***

### Record your own SOS message

The sos mesage is a wav file that will be automatically played when the system takes the default call actions (when the client is not able to skpeak or indicate who to call).
You should record it with a clear message, e.g. "Please help, there is an emergency at 5 Elm st.".

### Energy saving setup

As the pendant is intended to be a wireless battery powered device, the energy saving is very important.
The Raspberry Pi Zero W have a low idle consumption, but it is required to make it even lower, because of the small battery attached.

So it is recommended disable unused interfaces and services with the script:

```bash
cd snips-satellite-safe
./setup_battery_saving.sh
```

And when the system is ready and tested, disable ssh:

```bash
sudo raspi-config
		Interfacing Options -> SSH -> disabled
sudo reboot
```

To keep open an alternative communication way for troubleshooting, you can enable the UART service if you have a USB-console cable available:

```bash
sudo vi /boot/config.txt
    # Serial console
    enable_uart=1
```

### Final step, activate the service

This will disable the wi-fi communication (with `power_save=1`) and start the service:

```
sudo systemctl enable snips-safependant-server
```

## Dialogue flow

This is the conversation messages flow for a voice dialogue with the device.

<img src="https://github.com/maremoto/snips-resources-safe/blob/master/docs/SAFE%20dialogue.png" alt="SAFE dialogue">

## To Do

- [ ] Add low battery warning using the LBO pin.

## Copyright

This application is provided by [Alaba](https://www.alaba.io) as Open Source software. See [LICENSE](https://github.com/maremoto/snips-app-safe/blob/master/LICENSE) for more information.
