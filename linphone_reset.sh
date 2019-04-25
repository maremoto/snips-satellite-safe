#!/bin/bash

# 
# Failure recovery script to force back to normal after a call
#

function softreset()
{
 type linphonecsh > /dev/null 2>&1
  if [[ $? -eq 0 ]]
  then
      # end call
      echo " ... forcefully end call"
      linphonecsh generic terminate

      # unregister
      echo " ... unregister"
      linphonecsh unregister

      # end
      echo " ... stop daemon"
      linphonecsh exit
  else
      echo "WARNING NOT FOUND linphone command shell binary \"linphonecsh\""
  fi
}

function reset() {
   # snips audio server disabled by default
   sudo systemctl stop snips-audio-server
   sudo systemctl disable snips-audio-server

   # recover from faulty sessions
  sudo pkill linphonec 
}

function clean() {
  echo " ... cleaning "$1

  cd $1
  sudo rm -f .linphonerc
  sudo rm -f .linphone-zidcache
  sudo rm -f .local/share/linphone/linphone.db
  chmod 777 .local/share/linphone/

  cd - > /dev/null
  return
  
  linphonec <<:FIN
quit
:FIN
}


#
# MAIN
#
#softreset
reset
clean /root
clean ~

exit 0
