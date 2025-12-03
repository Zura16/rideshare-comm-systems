'''
Implementing lamport Logical Clock
this will ensure casual orderinh in distributed ride sharing
'''
import threading
class LamClock:
    # implement clock before local eveny, havin the curr clock value sentin every message, update clock to max when received
    def __init__(self, id):
        self.id = id
        self.time = 0
        self.lock = threading.Lock()

    def inccl(self):
        with self.lock:
            self.time +=1
            return  self.time
        
    def send(self):
        return  self.inccl()
    
    def updcl( self,  reci):
        with self.lock:
            self.time = max(self.time, reci) +1
            return self.time
        
    def gett ( self):
        with self.lock:
            return self.time
        
    def __str__(self):
        return f"[{self.id}: T{self.time}]"
    
    def __repr__(self):
        return f"LamportClock(id = '{self.id }', time={ self.time})"
    
class TimestampE:
        def __init__( self,event_type, data,tist, id):
            self.event_type =event_type
            self.data  = data
            self.tist =  tist
            self.id =id

        def __lt__(self,other):
            if self.tist!= other.tist:
                return self.tist< other.tist
            return self.id <other.id
        def __str__(self):
            return f"[T{self.tist}|{self.id}]{self.event_t}: {self.data}"
        
        def condic(self):
            return{"event_type":self.event_type, "data":self.data, "lamport_time": self.tist, "id": self.id}
        
        @classmethod
        def  fr_dic(cls,  d):
            return cls(event_type= d["event_type"], data= d["data"], 
                       tist =d["lamport_time"], id =d["id"] )
        
# just impleemting the main function for the lampost here

if __name__ ==  "__main__":
    print("="* 60)
    print( "L AMPORT CLOCK DEMONSTRATION")
    print("=" *60)
    
    # Create clocks for different nodes
    dri_c =LamClock("driver-101")
    ser_c=LamClock("server")
    pas_c= LamClock( "passenger-5001")
    
    print("\n--- Scenario 1: Local Events ---")
    print(f"Driver initial:  {dri_c}")
    
    # Driver performs local events
    t1 =dri_c.inccl( )
    print( f"Driver starts app: {dri_c}")
    
    t2 =dri_c.inccl()
    print(f"Driver goes online: { dri_c}")
    
    print("\n--- Scenario 2: Message Send/Receive ---")
    print(f"Passenger initial: {pas_c}")
    
    # Passenger sends ride request
    request_time=pas_c.send()
    print( f"Passenger sends ride request: {pas_c}")
    
    # Server receives request (delayed in network)
    ser_c.updcl(request_time)
    print(f"Server receives request: { ser_c}")
    
    # Server processes and responds
    response_time =ser_c.send()
    print(f"Server sends driver assignment: { ser_c } ")
    
    # Passenger receives response
    pas_c.updcl(response_time)
    print( f"Passenger receives assignment: { pas_c}")
    
    print("\n--- Scenario 3: Concurrent Events with Ordering ---")
    
    # Create events
    events = []
    
    # Driver sends GPS update
    gps_time =  dri_c.send()
    events.append(TimestampE("gps_update", {"lat": 33.77, "lng": -118.19}, 
                                   gps_time,  dri_c.id))
    print( f" Driver GPS update: {dri_c}")
    
    # Passenger cancels (happens concurrently, different physical time)
    cancel_time =  pas_c.send()
    events.append(TimestampE("ride_cancel", {"ride_id": "R1001"}, 
                                   cancel_time, pas_c.id))
    print(f"Passenger cancels: {pas_c}")
    
    # Server accepts ride (happened before cancel, but message delayed)
    accept_time  = ser_c.send()
    events.append(TimestampE("ride_accept", {"ride_id": "R1001", "driver_id": "driver-101"}, 
                                   accept_time,  ser_c.id))
    print(f"Server accepts ride: { ser_c}")
    
    # Sort events by Lamport timestamp (causal order)
    print( "\n--- Causal Order (sorted by Lamport time) ---")
    events.sort()
    for event in events:
        print(f"  {event}")
    
    print("\n--- Scenario 4: Detecting Causality Violations ---")
    
    # Simulating out-of-order message arrival
    print("\nMessages arrive in this physical order:")
    print("  1. Ride cancel (T=4)")
    print("  2. Ride accept (T=6)")
    print("  3. GPS update (T=3)")
    
    print("\nBut Lamport ordering reveals TRUE causal order:")
    print("  1. GPS update (T=3) - happened first")
    print("  2. Ride cancel (T=4) - happened second")
    print("  3. Ride accept (T=6) - happened last")
    
    print("\n" + "="*60)
    print("✓ Lamport timestamps ensure correct event ordering")
    print("  even when messages arrive out of order!")
    print("="*60)