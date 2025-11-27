import socket
import json
import threading
import time
from datetime import datetime
from ipc.Lamport_clock import LamClock, TimestampE

#Straight up copied imports from gps_ls.py
class Lock: ##Honestly unsure on what to name the class
    def __init__(self, id):
        self.id = id
        self.active_lock = None
        self.waiting = []

    def begin(self, requester, TimestampE): 
        if self.active_lock is None: #No lock
            self.active_lock = requester
            self.active_timestamp = TimestampE
            print("The new process has acquired the lock.")
            return True #Lock granted
        
        if TimestampE < self.active_timestamp: #If requester has earlier timestamp give it priority
            wait = self.active_lock #current active lock goes to waiting
            self.waiting.append(wait) #current lock goes to waiting
            self.active_lock = requester #active lock becomes the requester
            self.active_timestamp = TimestampE #active timestamp becomes the requester's timestamp

            print("The new process has priority over the current lock holder, and has taken the lock.") #Maybe change this to driver/client related
               
            return True 
        
        else: #The lock was not granted
            self.waiting.append(requester)
            print("The process has been queued")
            return False 

         
    
    def commit():
        pass 

    def abort():
        pass

        
        