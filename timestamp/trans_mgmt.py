import threading

class Lock: ##Honestly unsure on what to name the class
    def __init__(self, id):
        self.id = id
        self.active_lock = None
        self.waiting = []

    def request_lock(self, requester_id, timestamp):
        if self.active_lock is None: #No lock
            self.active_lock = requester_id
            self.active_timestamp = timestamp
            return True #Lock granted
        
        if timestamp < self.active_timestamp:
            self.active_lock = requester_id
            self.active_timestamp = timestamp
            self.waiting.append(requester_id)   
            return True 
        
        self.waiting.append((requester_id))
        self.waiting.sort()
        return False 
    
    def commit():
        pass 

    def abort():
        pass
    
        
        