# Routing Service (FastAPI) Placeholder
from flask import Flask, request, jsonify
import math, time

app  =Flask(__name__)
Dri = {"driver_27": {"lat": 34.00, "lon":-118.10, "available": True}}

def havers(a_la, a_lon, b_la, b_lo):
    R = 6371
    dla = math.radians(b_la  -a_la)
    dlo = math.radians(b_lo-a_lon)
    ala=  math.radians(a_la)
    bla = math.radians(b_la)
    c = math.sin(dla/ 2) **2 + math.cos(ala)* math.cos(bla) *math.sin(dlo/2) ** 2
    return 2* R *math.asin(math.sqrt(c))

@app.route("/request_ride", methods = ["POST"])
def ride_req():
    e = request.get_json()
    userla = float(e.get("lat"))
    userlon = float( e.get("lon"))
    closest = None
    mini = 1e9

    for dri_id , inf in Dri.items():
        dis = havers(userla, userlon, inf["lat"], inf["lon"])
        if inf["available"] and dis<  mini:
            mini = dis
            closest = dri_id

    if closest is None:
        return jsonify({"status": "no driver"}), 200
    eta_min = max(1, int((mini/  40)*60) )
    Dri[closest]["available"] =False
    return jsonify({"status": "ok", "driver_id": closest, "eta_minimum": eta_min})

@app.route("/eta/<driver_id>", methods= ["GET"])
def the_eta(Dri_id):
    inf=  Dri.get(Dri_id)
    if inf is None:
        return jsonify({"error": "No driver found"}), 404
    return jsonify({"driver_id": Dri_id, "available": inf["available"], "ts": time.time()}), 200

if __name__ == "__main__":
    app.run(port=5001, debug= True)