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
            print("The new process has acquired the lock.\n")
            return True #Lock granted
        
        if TimestampE < self.active_timestamp: #If requester has earlier timestamp give it priority
            wait = (self.active_lock, self.active_timestamp) #current active lock goes to waiting
            self.waiting.append(wait) #current lock goes to waiting
            self.active_lock = requester #active lock becomes the requester
            self.active_timestamp = TimestampE #active timestamp becomes the requester's timestamp

            print("The new process has priority over the current lock holder, and has taken the lock.\n") #Maybe change this to driver/client related
               
            return True 
        
        else: #The lock was not granted
            self.waiting.append((requester, TimestampE))
            print("The process has been queued\n")
            return False 

         
    
    def commit(self,requester):
        if requester != self.active_lock:
            print("The requester does not hold the lock, therefore cannot commit\n")
            return False 
        
        self.active_lock = None
        self.active_timestamp = None
        print("The lock is now free.\n") 

        if len(self.waiting) > 0: #Processes are still in the queue
            next_lock, next_timestamp = min(self.waiting, key=lambda x: x[1]) #Get the waiting process with the earliest timestamp
            self.waiting.remove((next_lock, next_timestamp)) #Removing the next process from waiting list

            self.active_lock = next_lock 
            self.active_timestamp = next_timestamp

            print("The lock has been committed and the next process in queue is now active. \n")
        else:
            print("The lock has been committed and is now free.\n")
        
        return True #Lock committed

    def abort(self, requester): #Abort the lock request or release the lock
        for i, (lock, timestamp) in enumerate(self.waiting): #finding the requester in the waiting list
            if lock == requester: #Maybe rename lock bc there's too many locks
                self.waiting.pop(i) #Removing the aborted process from waiting list
                print("Process was aborted while it was in the queue.\n")
                return True #Process was aborted
        
        if requester == self.active_lock: #Aborting the active process
            print("The process is being aborted while it's active\n")
            self.active_lock = None #Removing active locks
            self.active_timestamp = None #Removing active timestamp
        
        if len(self.waiting) > 0:
            next_lock, next_timestamp = min(self.waiting, key=lambda x: x[1]) #Get the waiting process with the earliest timestamp
            self.waiting.remove((next_lock, next_timestamp)) #Removing the next process from waiting list

            self.active_lock = next_lock 
            self.active_timestamp = next_timestamp

            print("The process was aborted and the one with the shortest timestamp is now active. \n")

        else:#No processes in the queue
            self.active_lock = None
            self.active_timestamp = None
            print("The process was aborted and the lock is now free.\n")
        return True
        
        