# Demo Client Placeholder
# this i solely for the cilent requests
import requests
print("Requesting a ride...")
res= requests.post("http://127.0.0.1:5001/request_ride", json={"lat":33.00, "lon":-118.10})
print(res.json())