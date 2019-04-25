#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import subprocess
from threading import Timer

from src.snipsTools   import SnipsConfigParser
from src.peripherals  import Button, Led, tracetime
from src.phone        import Phone
from src.snipsMPU     import SnipsMPU

VERSION = '0.1.0'

CONFIG_INI = 'config.ini'

# TODO repensar timers y ¿poner en config?
AUDIO_SERVER_STARTING_TIME = 1.5 # seconds
SLEEP_MODE_TIMEOUT = 2800 # seconds  (30 min)
IDLE_TIMEOUT = 120 # seconds

def audio_test():
    FORMAT = "S16_LE"
    RATE = "48000"
    SECS = "1"
    cmd = "/usr/bin/arecord -D default -q -c2 -r "+RATE+" -f "+FORMAT+" -t wav -V mono -d "+SECS+" -v test.wav > /dev/null 2>&1"
    print("audio test:",cmd)
    subprocess.call(cmd,shell=True)
    cmd = "/usr/bin/aplay -D default -q -t raw -r "+RATE+" -c 2 -f "+FORMAT+" -d "+SECS+" /dev/zero"
    print("audio test:",cmd)
    subprocess.call(cmd,shell=True)

# ============
# Get config 
# ============

class MyConfig():

    def __init__(self):

        config = SnipsConfigParser.read_configuration_file(CONFIG_INI).get('global')
        
            # Read commm configuration
        self.MQTT_ADDR_HOST = str(config.get('mqtt_host'))
        self.MQTT_ADDR_PORT = str(config.get('mqtt_port'))
        self.MQTT_ADDR = "{}:{}".format(self.MQTT_ADDR_HOST, self.MQTT_ADDR_PORT)
        self.SITE_ID = str(config.get('site_id'))
        
            # Read peripherals configuration
        self.BUTTON_GPIO = int(config.get('button_gpio_bcm'))
        self.BUTTON_BOUNCETIME_MS = int(config.get('button_bouncetime_ms'))
        self.LED_GPIO = int(config.get('led_gpio_bcm'))
        self.LED_GPIO = int(config.get('led_gpio_bcm'))
        self.POWER_SAVING = int(config.get('power_saving'))
        
        config = SnipsConfigParser.read_configuration_file(CONFIG_INI).get('secret')
        
            # Read customization configuration
        self.CLIENT_NAME = str(config.get('client_name'))

        config = SnipsConfigParser.read_configuration_file(CONFIG_INI).get('phone')

        # Read softphone configuration
        self.PHONE_CONFIG = str(config.get('softphone_config_file'))
        self.TIMEOUT_END = str(config.get('timeout_call_end'))
        self.CAPTURE_SNDC = str(config.get('capture_soundcard_name'))
        self.PLAYBACK_SNDC = str(config.get('playback_soundcard_name'))
        self.SOS_WAV = str(config.get('sos_message_wav'))
        self.SOS_TXT = str(config.get('sos_message_text'))

# ============
# Service
# ============

class SatelliteService(object):
    '''
    Service managing the awake/sleep status of the satellite
    '''

    def __init__(self):
        
        '''
        #TODO repensar
        audio_test()
        time.sleep(1)
        '''
        
        self.__c = MyConfig()
        
        self.__phone = Phone(self.__c.PHONE_CONFIG, self.__c.TIMEOUT_END, 
                             self.__c.CAPTURE_SNDC, self.__c.PLAYBACK_SNDC, self.__c.SOS_WAV, self.__c.SOS_TXT)

        self.__snipsMPU = SnipsMPU(self.__c.MQTT_ADDR_HOST, self.__c.MQTT_ADDR_PORT, self.__c.SITE_ID, self.__c.CLIENT_NAME, self.__phone)

        self.__button = Button(self.__c.BUTTON_GPIO, self._awake_mode, self.__c.BUTTON_BOUNCETIME_MS)
        self.__led = Led(self.__c.LED_GPIO)

        self.__sleep_timer = None
        self.__sleeping = False
        self._sleep_mode()

        print("\nsatellite system ready")

    def _awake_mode(self):
        '''
        Set the system in working mode
        and trigger an asisstance session
        '''

        self._set_sleep_timer() # the satellite will be back at sleep mode if something goes wrong

        was_sleeping = False
        if self.__sleeping :
            was_sleeping = True

            self.__led.on()
        
            if self.POWER_SAVING == 1:
                print("starting wifi")
                subprocess.call("sudo /sbin/ifup wlan0",shell=True)
                time.sleep(0.5)
        
            print("starting audio server")
            subprocess.call("sudo systemctl enable snips-audio-server",shell=True)
            subprocess.call("sudo systemctl start snips-audio-server",shell=True)
            time.sleep(AUDIO_SERVER_STARTING_TIME)
    
            self.__sleeping = False
            
        if self.__phone.is_calling():
            self.__phone.stop_call()
        elif was_sleeping:
            self.__snipsMPU.ask_for_help()
        else:
            self.__snipsMPU.alarm_off()
    
    def _sleep_mode(self):
        '''
        Set the system in low-power mode
        '''
        
        self._cancel_sleep_timer()
        
        self.__led.off()

        self.__snipsMPU.reset()
        
        print("stopping audio server")
        subprocess.call("sudo systemctl stop snips-audio-server",shell=True)
        subprocess.call("sudo systemctl disable snips-audio-server",shell=True)

        if self.POWER_SAVING == 1:
            print("stopping wifi")
            subprocess.call("sudo /sbin/ifdown wlan0",shell=True)

        self.__sleeping = True

    def _set_sleep_timer(self):
        '''
        Set timer to go to sleep
        '''
        self._cancel_sleep_timer() # precaution
        tracetime("TIMEON")
        self.__sleep_timer = Timer(SLEEP_MODE_TIMEOUT, self._sleep_mode) 
        self.__sleep_timer.start()
            
    def _cancel_sleep_timer(self):
        '''
        Cancel timer to go to sleep
        '''
        if self.__sleep_timer is not None:
            tracetime("TIMEOFF")
            self.__sleep_timer.cancel()
            del(self.__sleep_timer)
            self.__sleep_timer = None
        
    def check(self):
        '''
        Check the status to go to sleep, 
        invoked in Main
        '''
        
        if self.__sleeping or self.__phone.is_calling():
            #TODO vigilar la baja batería
            return
            
        idle_time = self.__snipsMPU.idle_time()
        
        if idle_time is None:
            self._sleep_mode()
        else:
            print(" ... idle_time %.2f" % (idle_time))
            if idle_time > IDLE_TIMEOUT:
                self._sleep_mode()
        
    def clear(self):
        '''
        Finish
        '''

        self._sleep_mode()
        self.__led.clear()
        self.__button.clear()
        print("satellite system cleared\n")
    
# ============
# Main 
# ============

if __name__ == '__main__':     # Program start from here
    try:
        srv = SatelliteService()
        while True:
            srv.check()
            time.sleep(IDLE_TIMEOUT/10)
            
    except KeyboardInterrupt:  # When 'Ctrl+C' is pressed, the child program destroy() will be  executed.
        srv.clear()

