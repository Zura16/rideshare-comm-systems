# cecs327-rideshare-comm-systems
Distributed ride-sharing platform demonstrating interprocess, remote, and message-based communication (CECS 327)

🧭 Project Setup Guide (for Teammates)
1️⃣ Prerequisites

Make sure you have these installed:

Tool	Minimum Version	Notes
Python	3.10+	Required for FastAPI, sockets, and ZeroMQ
Git	Latest	For cloning and version control
WSL / Linux / macOS	Recommended	Windows users can use WSL2
pip	Latest	Run python3 -m ensurepip --upgrade if needed
2️⃣ Clone the repository
git clone https://github.com/<YOUR_USERNAME>/cecs327-rideshare-comm-systems.git
cd cecs327-rideshare-comm-systems

3️⃣ Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate    # on Linux / WSL
# OR
.venv\Scripts\activate       # on Windows PowerShell


You should now see (.venv) in your terminal prompt.

4️⃣ Install dependencies
pip install -r requirements.txt


If the requirements.txt isn’t generated yet, you can install manually:

pip install fastapi uvicorn pyzmq requests

5️⃣ Run each communication model
🧩 Direct Communication (IPC)

Server (aggregator):

python ipc/aggregator_server.py


Client (driver):

python ipc/driver_client.py


You should see driver JSON data arriving at the server.

🌐 Remote Communication (REST API)

Start the API:

uvicorn rest.routing_service:app --reload --host 127.0.0.1 --port 8000


Test in another terminal:

curl "http://127.0.0.1:8000/health"
curl -X POST "http://127.0.0.1:8000/requestRide?pickup=CSULB&dropoff=Downtown"

📡 Indirect Communication (Pub/Sub)

Publisher (driver events):

python pubsub/publisher_driver.py


Subscriber (rider app):

python pubsub/subscriber_rider.py


Subscribers will print live ride.status updates.

6️⃣ (Optional) Run all modules at once

You can open three terminals:

Run the REST API (uvicorn ...)

Run the aggregator TCP server

Run the publisher/subscriber for live updates

It demonstrates all communication models in action.

7️⃣ Validation & Troubleshooting

If you get ModuleNotFoundError, check that the venv is activated.

If uvicorn isn’t found, reinstall it:

pip install uvicorn


If ZeroMQ fails:

pip install pyzmq


If a port is already in use, change it in the script (e.g., 5001 → 5002).

8️⃣ Contribution Workflow

Each teammate should:

git pull origin main
git checkout -b your-branch-name
# make changes
git add .
git commit -m "Added REST endpoints"
git push origin your-branch-name


Then open a Pull Request on GitHub.

9️⃣ Folder Structure
cecs327-rideshare-comm-systems/
│
├── ipc/         # TCP socket communication
├── rest/        # REST API (FastAPI)
├── pubsub/      # ZeroMQ publisher/subscriber
├── docs/        # Report, diagrams, validation logs
└── README.md

✅ Quick sanity check

Run these commands — you should get output for each:

python ipc/driver_client.py
curl http://127.0.0.1:8000/health
python pubsub/subscriber_rider.py


If you see messages, JSON, or ride events — you’re good.
