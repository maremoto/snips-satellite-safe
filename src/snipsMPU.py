#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime, time
#import subprocess

from hermes_python.hermes import Hermes
#from hermes_python.ontology.dialogue.intent import IntentMessage, IntentClassifierResult
#from hermes_python.ontology.dialogue.slot import SlotMap

CREATOR = "maremoto:"
INTENT_HELP_ME =      CREATOR + "helpMe"
INTENT_CALL_SOMEONE = CREATOR + "callSomeone"
INTENT_CALL_END =     CREATOR + "callEnd"
INTENT_CLEAR_ALARM =  CREATOR + "clearAlarm"
INTENT_END =          CREATOR + "everythingIsOk"

def ahora():
    then = datetime.datetime.now()
    return (time.mktime(then.timetuple())*1e3 + then.microsecond/1e3)/1000
  
def tracing_timestamp():
    return "[%s]" % (time.strftime("%H:%M:%S"))

class SnipsMPU(object):
    '''
    Client for MQTT protocol
    '''
    
    def __init__(self, mqtt_host, mqtt_port, site_id, client_name, phone):

        self.__mqtt_host = mqtt_host
        self.__mqtt_port = mqtt_port
        self.__mqtt_addr =  "{}:{}".format(mqtt_host, mqtt_port)
        self.__site_id = site_id
        self.__client_name = client_name
        self.__phone = phone
        
        self.__hermes = None        
        self.reset()

    def ask_for_help(self):
        '''
        helpMe message when button is pressed
        '''

        self.__last_activity_time = ahora()

            # Send the message to base
        print("messaging HELP to "+self.__mqtt_addr+" as "+self.__site_id)
        with Hermes(self.__mqtt_addr
                     ,rust_logs_enabled=True #TODO quitar
                    ) as h:
            cdata = INTENT_HELP_ME+","+self.__client_name # triggers helpMe intent in base
            h.publish_start_session_notification(
                                               site_id=self.__site_id, 
                                               session_initiation_text="",
                                               custom_data=cdata) 
            # Start checking the activity
        self._start_monitoring_activity()

    def _call_result(self, res):
        '''
        call ended with result=res
        '''
        self.__last_activity_time = ahora()

            # Send the message to base
        print("messaging CALL_RESULT "+str(res)+" to "+self.__mqtt_addr+" as "+self.__site_id)
        with Hermes(self.__mqtt_addr
                     ,rust_logs_enabled=True #TODO quitar
                    ) as h:
            cdata = INTENT_CALL_END+","+str(res) # triggers call result actions in base
            h.publish_start_session_notification(
                                               site_id=self.__site_id, 
                                               session_initiation_text="",
                                               custom_data=cdata) 

    def _session_queued(self, hermes, message):
        # because of the configuration, only satellite site_id messages are listened
        #if message.site_id != self.__site_id: return
        print("# Session Queued", message.site_id, message.custom_data, message.session_id)
        self.__last_activity_time = ahora()

    def _session_started(self, hermes, message):
        # because of the configuration, only satellite site_id messages are listened
        #if message.site_id != self.__site_id: return
        print("# Session Started", message.site_id, message.custom_data, message.session_id)
        self.__last_activity_time = ahora()

    def _session_ended(self, hermes, message):
        # because of the configuration, only satellite site_id messages are listened
        #if message.site_id != self.__site_id: return
        print("# Session Ended", ahora(), message.site_id, message.custom_data, message.session_id)
        self.__last_activity_time = ahora()
        
        custom_data = message.custom_data
        if custom_data is not None:
            acustom = custom_data.split(",")

                # Satellite should do a call
            if acustom[0] == INTENT_CALL_SOMEONE:
                name = acustom[1]
                number = acustom[2]
                if acustom[3] == "True" :   play_sos_message = True
                else:                       play_sos_message = False
                '''
                #TODO quitar porque no hace efecto
                # Toggle hotword off in satellites
                args="mosquitto_pub -h %s -p %s -t 'hermes/hotword/toggleOff' -m '{\"siteId\": \"%s\"}'" % (self.__mqtt_host,
                                                                                                              self.__mqtt_port,
                                                                                                              self.__site_id)
                subprocess.call(args,shell=True)
                '''

                self.__phone.start_call(name, number, self._call_result, play_sos_message=play_sos_message)

                # Go to sleep
            elif acustom[0] == INTENT_END:
                self.__last_activity_time = None

    def _activity(self, hermes, message):
        # because of the configuration, only satellite site_id messages are listened
        #if message.site_id != self.__site_id: return
        print("# Intent Received", ahora(), message.site_id, message.intent.intent_name, message.custom_data, message.session_id)
        self.__last_activity_time = ahora()

    def _start_monitoring_activity(self):
        '''
        track mqtt bus activity
        '''

        if self.__hermes is not None:
            return # already tracking
        
            # Subscribe to messages
        print("subscribing to "+self.__mqtt_addr+" as "+self.__site_id)
        with Hermes(self.__mqtt_addr
                     ,rust_logs_enabled=True #TODO quitar
                    ) as h:
            self.__hermes = h
            h.subscribe_session_ended(self._session_ended) \
                .subscribe_session_started(self._session_started) \
                .subscribe_session_queued(self._session_queued) \
                .subscribe_intents(self._activity) \
                .loop_start()

    def alarm_off(self):
        '''
        button pushed for alarm off
        '''
        self.__last_activity_time = ahora()

            # Send the message to base
        print("messaging ALARM_OFF to "+self.__mqtt_addr+" as "+self.__site_id)
        with Hermes(self.__mqtt_addr
                     ,rust_logs_enabled=True #TODO quitar
                    ) as h:
            cdata = INTENT_CLEAR_ALARM # triggers call result actions in base
            h.publish_start_session_notification(
                                               site_id=self.__site_id, 
                                               session_initiation_text="",
                                               custom_data=cdata)         

    def reset(self):
        if self.__hermes is not None:
            self.__hermes.loop_stop()
            self.__hermes = None
        self.__last_activity_time = None
        
    def idle_time(self):
        if self.__phone.is_calling():
            self.__last_activity_time = ahora()
        if self.__last_activity_time is not None:
            return ahora() - self.__last_activity_time 
        else:
            return None
             