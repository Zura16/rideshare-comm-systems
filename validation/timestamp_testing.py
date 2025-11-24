# basically, this one's just gona be for testing purposes to check the lamport
# having netwrok delays and concurrent ordering 
import socket
import json
import time
import random
import threading
from ipc.Lamport_clock import LamClock, TimestampE

DISPATCHER_HOST = "127.0.0.1"
DISPATCHER_PORT = 5000

class RideEventSimulator:
    
    def __init__(self , id):
        self.clock = LamClock( id)
        self.id = id
        self.socket  = None
        
    def con(self ):
        
        try:
            self.socket= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect( (DISPATCHER_HOST, DISPATCHER_PORT))
            print(f"{self.clock} Connected to server\n")
            return True
        except Exception as e:
            print(f"{self.clock } Connection failed: {  e}")
            return False
    
    def send_e(self,  event_type, data, delay=0):
       
        if delay > 0:
            print(f"{self.clock} [DELAYED {delay }s] Preparing {event_type}...")
            time.sleep( delay)
        
        timestamp = self.clock.send()
        event = TimestampE(event_type,  data, timestamp,self.id)
        
        message = json.dumps(event.condic() ) + "\n"
        self.socket.sendall(message.encode( 'utf-8') )
        
        print(f"{self.clock } Sent: {event_type} - {data }")
        
        # Reading acknowledments for the server
        try:
            ack_line = self.socket.makefile().readline().strip()
            if ack_line:
                ack = json.loads( ack_line)
                if "lamport_time" in ack:
                    ser_t = ack[ "lamport_time"]
                    self.clock.updcl(ser_t)
                    print(f"{self.clock} ACK received (server at T{ ser_t})\n")
        except:
            pass
    
    def close(self):

        if self.socket :
            self.socket.close()


def sce1_seq_cau():
    
    print("\n" +"="*70 )
    print("SCENARIO 1: Sequential Ride Lifecycle (Causal Order)")
    print("="* 70 +"\n")

    passenger = RideEventSimulator( "passenger-P001")
    driver = RideEventSimulator("driver-D001" )
    
    if not passenger.con() or not  driver.con():
        return
    
    try:
        # this is where the passengers are requesting a ride
        passenger.send_e("ride_request", { 
            "ride_id": "R1001",
            "pickup": {"lat": 33.77, "lng": -118.19}, 
            "dropoff": {"lat": 33.80, "lng": -118.22}
        } )
        time.sleep(1)
        
        # this is where the drive accepts 
        driver.send_e("ride_accept",{
            "ride_id" : "R1001",
            "driver_id": "driver-D001",
            "eta_min": 5
        })
        time.sleep(1)
        
        # this is where the driver is stariting the trip
        driver.send_e("trip_start", {
            "ride_id": "R1001",
            "start_time": time.time()
        })
        time.sleep(2)
        
        # this is where the driver completes the trip
        driver.send_e( "trip_complete", {
            "ride_id": "R1001",
            "end_time": time.time() ,
            "fare": 15.50
        })
        
        print("\n✓ Scenario 1 Complete")
        print("  Expected: request < accept < start < complete")
        print("  Lamport timestamps should reflect this causal order\n")
        
    finally:
        passenger.close()
        driver.close()


def sce2_net_del():
    
    print("\n" + "="*70)
    print("SCENARIO 2: Network Delays (Messages Arrive Out of Order)")
    print("="*70 + "\n")
    
    passenger = RideEventSimulator( "passenger-P002")
    driver = RideEventSimulator("driver-D002")
    server_sim = RideEventSimulator("server")
    
    if not passenger.con() or not driver.con() or not server_sim.con():
        return
    
    try:
        print( "Sending events with artificial network delays:")
        print("  Event A: Passenger requests (no delay)")
        print("  Event B: Server assigns driver (3s delay)")
        print("  Event C: Driver goes online (1s delay)")
        print()
        

        def send_request():
            passenger.send_e("ride_request" , {
                "ride_id": "R2001",
                "passenger_id": "P002" 
            }, delay=0)
        
        def send_assignment():
            server_sim.send_e( "driver_assigned", {
                "ride_id": "R2001" ,
                "driver_id": "D002"
            }, delay=3 )
        
        def send_online():
            driver.send_e(" driver_online", {
                "driver_id": "D002",
                "location": { "lat":33.78, "lng": -118.20 }
            }, delay=1 )
        
        # having all the threads start at the same time
        t1  = threading.Thread( target=send_request)
        t2 =  threading.Thread(target=send_assignment)
        t3= threading.Thread( target=send_online)
        
        t1.start()
        t2.start()
        t3.start()
        
        t1.join()
        t2.join()
        t3.join()
        
        print("\n✓ Scenario 2 Complete")
        print("  Physical arrival order: A → C → B (due to delays)")
        print("  Causal order (Lamport): Check server log for correct ordering")
        print("  Demonstrates why logical timestamps are necessary!\n" )
        
    finally:
        passenger.close()
        driver.close()
        server_sim.close()


def sce3_con_eve():
    #having updates at same time from multiple drivers
    print("\n"+ "=" *70)
    print("SCENARIO 3: Concurrent GPS Updates (Multiple Drivers)")
    print("="*70 +"\n")
    
    n_dri = 5
    drivers = []
    
    # Create and connect drivers
    for i in range( n_dri):
        driver = RideEventSimulator(f"driver-D10{i}")
        if driver.con():
            drivers.append(driver )
    
    if not drivers:
        print("Failed to connect drivers")
        return
    
    try:
        print(f"Sending concurrent GPS updates from {len(drivers)} drivers...\n")
        
        def send_gps_updates(d_sim, count=3):

            lat, lng = 33.77 + random.uniform(-0.01, 0.01), -118.19 + random.uniform(-0.01, 0.01)
            
            for i in range(count):
                d_sim.send_e("gps_update", {
                    "driver_id": d_sim.id,
                    "lat": lat + (i * 0.001),
                    "lng": lng + (i * 0.001),
                    "speed_kmh": 35 + random.uniform(-5, 5),
                    "status": "available"
                })
                time.sleep(random.uniform(0.5, 1.5))
        
        threads = []
        for driver in drivers:
            t = threading.Thread(target=send_gps_updates, args=(driver, 3))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        print("\n✓ Scenario 3 Complete")
        print(f"  {len(drivers)} drivers sent concurrent GPS updates")
        print("  Server should order them causally by Lamport timestamps\n")
        
    finally:
        for driver in drivers:
            driver.close()


def scenario_4_emergency_alert():
    #emergency alert
    print("\n" + "="*70)
    print("SCENARIO 4: Emergency Alert Ordering")
    print("="*70 + "\n")
    
    driver=  RideEventSimulator("driver-D003")
    passenger =RideEventSimulator( "passenger-P003")
    emergency = RideEventSimulator("emergency-service" )
    
    if not driver.con()  or not passenger.con() or not emergency.con():
        return
    
    try:
        driver.send_e("gps_update",  {
            "lat": 33.77, "lng": -118.19,
            "status":  "on_trip"
        })
        time.sleep(0.5)
    
        passenger.send_e("emergency_alert", {
            "ride_id": "R3001",
            "alert_type": "accident",
            "severity": "high",
            "location": {"lat": 33.77, "lng" : -118.19}
        })
        time.sleep(0.5)
        #resomse to emeergency
        emergency.send_e("emergency_response", {
            "alert_id": "E001",
            "responding_unit": "Unit-51" ,
            "eta_min": 3
        })
        time.sleep(0.5)
        
        # driver sends status
        driver.send_e("driver_status", {
            "status": "emergency_stop",
            "location": {"lat": 33.77, "lng": -118.19}
        })
        
        print("\n✓ Scenario 4 Complete")
        print("  Emergency events are timestamped and ordered causally")
        print("  Critical for coordinating emergency response\n")
        
    finally:
        driver.close()
        passenger.close()
        emergency.close()


def run_all_scenarios():
    #running all the tests
    print("\n" + "="*70)
    print("LAMPORT TIMESTAMP TEST SUITE" )
    print( "Testing Causal Event Ordering in Distributed Ride-Sharing System")
    print("="* 70)
    
    input("\n Press Enter to start Scenario 1...")
    sce1_seq_cau()
    
    input("\nPress Enter to start Scenario 2...")
    sce2_net_del()
    
    input("\n Press Enter to start Scenario 3...")
    sce3_con_eve()
    
    input("\nPress Enter to start Scenario 4..." )
    scenario_4_emergency_alert()
    
    print("\n" + "="* 70)
    print("ALL SCENARIOS COMPLETE" )
    print(" Check server output for causal event ordering analysis")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        run_all_scenarios()
    except KeyboardInterrupt:
        print("\n\nTest suite interrupted")
    except Exception as e:
        print(f"\nError running scenarios: {e}")