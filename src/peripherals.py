#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import RPi.GPIO as GPIO
import datetime, time

def tracetime(txt):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), txt))

class Led(object):
    '''
    Led for feedback
    '''

    def __init__(self, led_pin):
        self.__led_pin = led_pin
        self.__led_status = 0
        self._gpio_init()

    def _gpio_init(self):
        GPIO.setmode(GPIO.BOARD)        # Numbers GPIOs by physical location
        GPIO.setwarnings(False)         # Discard warnings

        GPIO.setup(self.__led_pin, GPIO.OUT)   # Set LedPin's mode is output
        GPIO.output(self.__led_pin, GPIO.LOW) # Set LedPin low (ground) to off led

    def on(self):
        self.__led_status = 1
        GPIO.output(self.__led_pin, self.__led_status)  # switch led status(off-->on) high(+3.3V) 
        tracetime('[Led] on')

    def off(self):
        self.__led_status = 0
        GPIO.output(self.__led_pin, self.__led_status)  # switch led status(on-->off)
        tracetime('[Led] off')

    def is_on(self):
        return self.__led_status == 1

    def clear(self):
        self.off()
        GPIO.cleanup()    

class Button(object):
    '''
    Button for start assistance
    '''
    
    def __init__(self, gpio_pin, push_callback, bouncetime):
        self.__gpio_pin = gpio_pin
        self.__push_cb = push_callback
        self.__bouncetime = bouncetime
        
        self.__last_execution = self._get_time()
        self._gpio_init()

    def _get_time(self):
        then = datetime.datetime.now()
        return (time.mktime(then.timetuple())*1e3 + then.microsecond/1e3)/1000

    def _gpio_init(self):
        GPIO.setmode(GPIO.BOARD)        # Numbers GPIOs by physical location
        GPIO.setwarnings(False)         # Discard warnings

        GPIO.setup(self.__gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)    # Set BtnPin's mode is input, and pull up to high level(3.3V)
            # wait for falling and set bouncetime to prevent the callback function from being called multiple times when the button is pressed
        GPIO.add_event_detect(self.__gpio_pin, GPIO.FALLING, callback=self._push, bouncetime=self.__bouncetime)

    def _push(self, ev=None):
        if 1000*(self._get_time() - self.__last_execution) <= self.__bouncetime:
            #print("[Button] has been pushed and DISCARDED",self._get_time(),self._last_execution)
            return # re-pushing too quick
        else:
            tracetime("[Button] has been pushed")
            
        self.__push_cb() # acción sustanciosa
        self.__last_execution = self._get_time()

    def clear(self):
        GPIO.cleanup()    
