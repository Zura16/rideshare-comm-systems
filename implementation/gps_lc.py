# for casual ordering, we have gps updates sent with logical time
# driver Gps client with lamport timestamp integration
import socket
import json
import time
import random
import sys
import os
from Lamport_clock import LamClock, TimestampE



DISPATCHER_HOST =  "127.0.0.1"
DISPATCHER_PORT= 5001

def jit(val, spread= 0.0008):
    
    return val +random.uniform(-spread, spread)

def si_dri_wi_lam( drid, stlat,stlng):
    
    clock = LamClock( drid)
    
    stycle = ["available",  "enroute", "available"]
    i = 0
    
    try:
        with socket.socket( socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(( DISPATCHER_HOST, DISPATCHER_PORT))
            print(f"{clock} Connected to dispatcher \n")
            
            lat, lng = stlat, stlng
            speed = 35.0
            
            while True:
                # having lamport implemeted for local event
                tist =  clock.send()
                
                status  =stycle[i % len(stycle)]
                
                # making gps update
                gps_data= {"driver_id": drid, "lat": jit(lat),
                    "lng": jit(lng),"speed_kmh": max(0.0,speed +random.uniform(-5,5 ) ),"status": status
                }
                
                event =TimestampE(event_type ="gps_update",data= gps_data,tist=tist,id  = drid
                )
                
                # Send as JSON
                message = json.dumps(event.condic()) + "\n"
                s.sendall(message.encode("utf-8"))
                
                print(f"{clock} GPS Update sent: ({ gps_data['lat']:.4f}, {gps_data['lng']:.4f}) "
                      f"Status: { status}")
                
                # reading the ack with server's time
                try:
                    ack_line=  s.makefile().readline().strip()
                    if ack_line:
                        ack = json.loads(ack_line)
                        
                        # updating the clock based on server's ts
                        if "lamport_time"  in ack:
                            server_time = ack["lamport_time"]
                            clock.updcl(server_time )
                            print(f" {clock } ACK received (server was at T{server_time})\n")
                        else:
                            print(f"{clock} ACK:  {ack.get( 'status', 'ok')}\n")
                            
                except json.JSONDecodeError:
                    pass
                except Exception as  e:
                    print(f"{ clock} Error reading ACK: {e }\n")
                

                lat +=0.0009
                lng +=0.0006
                i  += 1
                
                time.sleep(1.0)
                
    except  KeyboardInterrupt:
        print( f"\n{clock} Shutting down gracefully...")
    except ConnectionRefusedError:
        print( f"{ clock} ERROR: Could not connect to dispatcher at {DISPATCHER_HOST}:{DISPATCHER_PORT}")
        print("Make sure the GPS server is running first!")
    except Exception as e:
        print(f"{clock} ERROR: { e}")
    finally:
        print(f"{ clock} Disconnected")


if __name__ == "__main__":
   
    if len(sys.argv) < 2:
        print("Usage: python gps_lamport_client.py <driver_id> [start_lat] [start_lng]")
        print("Example: python gps_lamport_client.py driver-101")
        sys.exit(1)
    
    driver_id = sys.argv[1]
    start_lat = float(sys.argv[2]) if len(sys.argv) > 2 else 33.7701
    start_lng = float(sys.argv[3]) if len(sys.argv) > 3 else -118.1937
    
    start_lat += random.uniform(-0.01, 0.01)
    start_lng += random.uniform(-0.01, 0.01)
    
    print("="*70)
    print(f"DRIVER GPS CLIENT WITH LAMPORT TIMESTAMPS")
    print(f"Driver ID: {driver_id}")
    print(f"Starting Position: ({start_lat:.4f}, {start_lng:.4f})")
    print("="*70 + "\n")
    
    si_dri_wi_lam(driver_id, start_lat, start_lng)