#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#import re
import os
import subprocess
from subprocess import PIPE, STDOUT
import time
import threading

RESULT_END=0
RESULT_FAILURE=1
RESULT_FATAL=2

SOS_TXT_TIMES=3
TIMEOUT_END_SOS_CALL=30

def tracetime(txt):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), txt))

class Phone(object):
    '''
    Call for Assistance
    '''

    def __init__(self, config_file, timeout_call_end, 
                 capture_soundcard_name, playback_soundcard_name, sos_message_wav, sos_message_text):
        self.__softphone_config_file = config_file
        self.__timeout_end = int(timeout_call_end)
        self.__capture_sndc = capture_soundcard_name
        self.__playback_sndc = playback_soundcard_name
        self.__sos_wav = sos_message_wav
        self.__sos_txt = sos_message_text

        self._no_call_status()
        
    def _no_call_status(self):
        self.__calling_contact = None
        self.__calling_number = None
        self.__calling_site_id = None
        self.__play_sos_message = False
        self.__result_cb = None
        self.__manually_terminated = False
        self.__call_proc = None
        self.__check_timer = None

    '''
    def _is_result_end(res):
        return res == RESULT_END
    def _is_result_failure(res):
        return res == RESULT_FAILURE
    def _is_result_fatal(res):
        return res == RESULT_FATAL
        '''

    def _ended_call(self, res):
        time.sleep(3) # avoid race conditions
        if self.__result_cb is not None:
            self.__result_cb(res)
        else:
            print("WEIRD NO END CALLBACK")
        self._no_call_status()
    
    def _check_call(self):
        if self.__call_proc is None: return
           
            # check and read output
        rc = self.__call_proc.poll()
        txt = self.__call_proc.stdout.readline()
        print(txt, end=" ")

        #TODO borrar esto, NO SE PUEDE PORQUE EL AUDIO SE CORTA Y LA LLAMADA SE ACABA
        '''
        connected = False
        if re.search('StreamsRunning', txt): connected = True
        condition1 = (self.__sos_wav == "" or self.__sos_wav is None)
        condition2 = (self.__sos_txt != "" and self.__sos_txt is not None)
        if self.__play_sos_message and condition1 and condition2 and connected :
            sentence = " . ".join(x for x in [ self.__sos_txt ]* SOS_TXT_TIMES)
            print("  play sos message","("+str(SOS_TXT_TIMES)+"times):",self.__sos_txt)
            if self.__inform_cb is not None: 
                self.__inform_cb(sentence=sentence)
            self.__play_sos_message = False
            print("  and finish the call in",str(TIMEOUT_END_SOS_CALL),"seconds")
            t = threading.Timer(TIMEOUT_END_SOS_CALL, self.stop_call) # automatic end of call
            t.start()
            '''
        
        if self.__call_proc.returncode is not None:
                # ended call
            print(self.__call_proc.stdout.read(), end=" ")
            res = rc
            if res > RESULT_FATAL or res < RESULT_END: 
                res = RESULT_FATAL
            if self.__manually_terminated:
                res = 0
            print("CALL RESULT",rc,"->",res)
            self._ended_call(res)
        else:
                # ongoing call, keep checking
            self.__check_timer = threading.Timer(0.5, self._check_call)
            self.__check_timer.start()
        
    def start_call(self, name, number, result_cb, play_sos_message=False):
        '''
        Call the selected contact, invoked when the audio session is over with the "calling..." message
        '''
        if self.__calling_number is not None: 
            #TODO llamar a callback con fallo o algo, que hay una llamada en curso
            return ""

        self.__calling_contact = name
        self.__calling_number = number
        self.__result_cb = result_cb
        self.__play_sos_message = play_sos_message

        print("Calling to", self.__calling_contact, self.__calling_number)

        #usage: ./linphone_call.sh [-v(erbose)] [-m <wav>] [-t <end_timeout_s>] [-p <playback_soundcard_name>] [-c <capture_soundcard_name>] <conf_file> <contact_number>
        working_dir = os.getcwd()
        # TODO remove -v (verbosity) when tests end
        args = [working_dir+"/linphone_call.sh", "-v" ,"-t", str(self.__timeout_end)]
        if self.__play_sos_message:
            if self.__sos_wav != "":
                args = args + ["-m", self.__sos_wav]
            else:
                print("WEIRD no configured sos_message_wav file")
        if self.__playback_sndc != "":
            args = args + ["-p", self.__playback_sndc]
        if self.__capture_sndc != "":
            args = args + ["-c", self.__capture_sndc]
        args = args + [self.__softphone_config_file, number]
        print("CALL EXEC",' '.join(x for x in args))
        
        try:
            '''
            args = ' '.join(x for x in args)
            self.__call_proc = subprocess.Popen(args, stdout=PIPE, stderr=STDOUT, universal_newlines=True, 
                                                shell=True)
            '''
            self.__call_proc = subprocess.Popen(args, stdout=PIPE, stderr=STDOUT, universal_newlines=True, 
                                                shell=False)
            self._check_call()

        except Exception as e:
            print("CALL EXCEPTION",e)
            self._ended_call(RESULT_FATAL)

    def stop_call(self):
        '''
        Interrupt call forcefully
        '''
        if self.__call_proc is None: return
        
        self.__manually_terminated = True
        self.__call_proc.terminate()

    def is_calling(self):
        return self.__call_proc is not None
        
    def is_ready_to_call(self):
        return self.__calling_number is not None and not self.is_calling()
        