import dotenv
import http.client
import json
import os

dotenv.load_dotenv()
API_KEY = os.getenv("API_KEY")

conn = http.client.HTTPSConnection("polkadot.api.subscan.io")
headers = {
   'User-Agent': 'Apidog/1.0.0 (https://apidog.com)',
   'Content-Type': 'application/json',
   'X-API-Key': API_KEY
}

def get_events(page):
	payload = json.dumps({
		"module": "xcmPallet", "event_id": "attempted",
		"order": "desc",
		"page": page,
		"row": 100
	})
	conn.request("POST", "/api/v2/scan/events", payload, headers)
	res = conn.getresponse()
	data = res.read()
	data = data.decode("utf-8")
	return json.loads(data)["data"]["events"]

total = []

if os.path.exists("xcm-events.json"):
	with open("xcm-events.json", "r") as f:
		total = json.load(f)
	print(f"Loaded {len(total)} events from cache")
else:
	page = 0
	while True:
		events = get_events(page)
		page = page + 1
		if events is None or len(events) == 0:
			print("No more events")
			break
		total = total + events
		print(f"Got {len(events)} events, total {len(total)}")

		with open("xcm-events.json", "w") as f:
			json.dump(total, f)

def get_event_params(id):
	payload = json.dumps({
		"event_index": id,
	})
	conn.request("POST", "/api/scan/event", payload, headers)
	res = conn.getresponse()
	data = res.read()
	data = data.decode("utf-8")
	return json.loads(data)["data"]

params_list = {}
for event in total:
	id = event["event_index"]
	params = get_event_params(id)
	
	if "FailedToTransactAsset" in str(params):
		params_list[id] = params
		print(f"[{id}] {params}")

with open("xcm-params.json", "w") as f:
	json.dump(params_list, f)

os._exit(0)

extrinsics = {}
for event in total:
	extrinsics[event["extrinsic_index"]] = event

def get_extrinsic(id):
	payload = json.dumps({
		"extrinsic_index": id,
    	"only_extrinsic_event": True
	})
	conn.request("POST", "/api/scan/extrinsic", payload, headers)
	res = conn.getresponse()
	data = res.read()
	data = data.decode("utf-8")
	return json.loads(data)["data"]

blocks = []
for id, extrinsic in extrinsics.items():
	ext = get_extrinsic(id)
	params = ext["params"]
	name = ""
	for param in params:
		value = param["value"]
		if type(value) is dict and "call_module" in value:
			name += value["call_module"] + "::" + value["call_name"] + " "
	if name != "":
		print(f"[{id}] {name}")
		blocks.append(id)

with open("sudo-blocks.json", "w") as f:
	json.dump(blocks, f)
