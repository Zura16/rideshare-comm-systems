# gps aggrgate server with Lamport
# maintains event log and gps updates

import socket
import json
import threading
import time
from datetime import datetime
from ipc.Lamport_clock import LamClock, TimestampE

class GPSAggregatorWithLamport:
    def __init__( self, h='127.0.0.1', p=5000):
        self.h= h
        self.p =p
        self.clock=LamClock("gps-server")
        
        # driver's curr location
        self.drivers =  {}
        self.drivers_lock=  threading.Lock()
        
        #casual ordering event
        self.event_log=  []
        self.event_lock =threading.Lock()
        
        self.running =False
        
    def start(self):
        #starting the gps agg server
        self.running= True
        serso =socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serso.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serso.bind(( self.h,self.p))
        serso.listen(10)
        
        print(f"{self.clock}  GPS Aggregator Server started")
        print(f"Listening on {self.h }:{ self.p}")
        print("="* 70 +"\n")
        
        # stats thread
        sta_th= threading.Thread( target=self.p_stats )
        sta_th.daemon =  True
        sta_th.start()
        
        # event ord analysis thread
        ordering_thread = threading.Thread(target=self.ana_eve_ord )
        ordering_thread.daemon  =True
        ordering_thread.start()
        
        try:
            while  self.running:
                client_socket,  address =serso.accept()
                
                # having different threads for diff clients
                client_thread = threading.Thread(
                    target=self.handle_client ,
                    args=(client_socket, address )
                )
                client_thread.daemon =True
                client_thread.start()
                
        except KeyboardInterrupt:
            print( f"\n {self.clock } Shutting down...")
        finally:
            serso.close()
            self.pri_fi_eve_lo()
    
    def handle_client(self, cliso, add):
        driver_id =None
        
        try:
            file_obj =  cliso.makefile( 'r')
            
            while self.running :
                line = file_obj.readline()
                if not line:
                    break
                
                try:
                    # Parse timestamped event
                    event_dict= json.loads( line.strip())
                    event  = TimestampE.fr_dic(event_dict )
                    
                    driver_id = event.data.get('driver_id')
                    
                    # Update Lamport clock on receive
                    old_time =self.clock.gett()
                    new_time = self.clock.updcl(event.timestamp)
                    
                    # Log the event
                    with self.event_lock:
                        self.event_log.append(event )
                    
                    # Update driver location
                    with self.drivers_lock:
                        self.drivers[driver_id] = { 
                            'lat': event.data.get( 'lat') ,
                            'lng': event.data.get('lng' ),
                            'speed_kmh': event.data.get('speed_kmh') ,
                            'status': event.data.get('status') ,
                            'last_update':  datetime.now().isoformat(),
                            'last_lamport': event.timestamp, 
                            'address': add 
                        }
                    
                    print(f"{self.clock } Received from {driver_id}: "
                          f"({event.data.get('lat'):.4f}, {event.data.get('lng'):.4f}) "
                          f"[Driver T{event.tist }] "
                          f"(Server: T{old_time }→T{new_time})")
                    
                    # Send ACK with current server timestamp
                    ack_time = self.clock.send()
                    ack = {
                        'status': 'received',
                        'lamport_time': ack_time,
                        'server_node': self.clock.id
                    }
                    cliso.sendall( ( json.dumps(ack) + "\n").encode('utf-8'))
                    
                except json.JSONDecodeError as e:
                    print(f"{self.clock} Invalid JSON from {add}: {e}")
                except Exception as e:
                    print(f"{self.clock } Error processing event: {e}")
                    
        except Exception as e:
            print(f"{self.clock } Connection error with {add}: {e}")
        finally:
            if driver_id:
                with self.drivers_lock:
                    if driver_id in self.drivers:
                        del self.drivers[driver_id ]
                print(f"{self.clock} Driver {driver_id} disconnected")
            cliso.close()
    
    def p_stats(self ):
        while self.running:
            time.sleep(15 )
            
            with self.drivers_lock:
                active = len( self.drivers)
            
            with self.event_lock:
                total_events = len( self.event_log)
            
            print(f"\n{'='*70}")
            print(f"{self.clock} STATISTICS")
            print(f"  Active Drivers: {active}")
            print(f"  Total Events Logged: {total_events}")
            
            if active > 0:
                with self.drivers_lock:
                    print(f"  Drivers:")
                    for did, data in self.drivers.items():
                        print(f"   - {did}: {data['status']} at "
                              f"({data['lat']:.4f}, {data['lng']:.4f}) "
                              f"[Last T{data['last_lamport']}]")
            
            print(f"{'='*70}\n ")
    
    def ana_eve_ord(self):
        while self.running:
            time.sleep(20)
            
            with self.event_lock:
                if len(self.event_log ) < 2:
                    continue
            
                recent = self.event_log[-20:] if  len(self.event_log) > 20 else self.event_log[:]
                
                # sorting by lamport timestamp
                sorted_events = sorted( recent, key=lambda e: (e.timestamp, e.node_id))
                
                print(f"\n{'='*70}")
                print(f"{self.clock } CAUSAL EVENT ORDERING (Last 20 events)")
                print(f"{'='*70}")
                
                for i, event in enumerate(sorted_events, 1):
                    print(f"  {i:2d}. [T{event.timestamp:3d}] {event.node_id:15s} "
                          f"- { event.event_type}")
                
        
                physical_order = recent
                causal_order = sorted_events
                
                if physical_order != causal_order:
                    print(f"\nCAUSAL REORDERING DETECTED!")
                    print(f"  Physical arrival order ≠ Causal order (Lamport timestamps)")
                    print(f"  This demonstrates why logical clocks are necessary.")
                else:
                    print(f"\n  ✓  Events arrived in causal order")
                
                print(f"{'='*70}\n")
    #final printing
    def pri_fi_eve_lo(self):
        print(f"\n{'='*70}")
        print(f"{self.clock} FINAL EVENT LOG (Causally Ordered)")
        print(f"{'='*70}")
        
        with self.event_lock:
            if not self.event_log:
                print("  ( No events logged)")
                return
            
            sorted_events = sorted( self.event_log, key=lambda e: (e.timestamp, e.node_id))
            
            print(f"Total Events: {len(sorted_events)}\n")
            
            for i, event in enumerate( sorted_events, 1):
                print(f"  {i:4d }. [T{event.timestamp:4d}] {event.node_id:15s} "
                      f"at ({ event.data.get('lat', 0):.4f}, {event.data.get('lng', 0):.4f})")
                
                if i >= 50:  # Limit output for readability
                    print(f"  ... (showing first 50 of {len(sorted_events)} events)")
                    break
        
        print(f"{'='*70}\n")

if __name__ == "__main__":
    server =  GPSAggregatorWithLamport()
    server.start()