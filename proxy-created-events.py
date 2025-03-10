import dotenv
import http.client
import json
import os

OUT_FILE = "pure-proxy-created-events.json"

dotenv.load_dotenv()
API_KEY = os.getenv("API_KEY")

# Read the events from the file
if os.path.exists(OUT_FILE):
	with open(OUT_FILE, "r") as f:
		events = json.load(f)
else:
	events = []

if len(events) == 0:
	conn = http.client.HTTPSConnection("assethub-polkadot.api.subscan.io")
	headers = {
		'Content-Type': 'application/json',
		# Uncomment if you have a Subscan API Key
		#'X-API-Key': API_KEY
	}

	def get_events(page):
		payload = json.dumps({
			"module": "proxy",
			"event_id": "PureCreated",
			"order": "desc",
			"page": page,
			"row": 100,
		})
		conn.request("POST", "/api/v2/scan/events", payload, headers)
		res = conn.getresponse()
		data = res.read()
		data = data.decode("utf-8")
		events = json.loads(data)["data"]["events"]
		# only those that dont have an extrinsic index
		if events is None:
			return []

		return events

	def get_params(event_ids: list[int]):
		payload = json.dumps({
			"event_index": event_ids,
		})
		conn.request("POST", "/api/scan/event/params", payload, headers)
		res = conn.getresponse()
		data = res.read()
		data = data.decode("utf-8")
		
		return json.loads(data)["data"]

	def get_proxy_created_events():
		page = 0
		events = []
		while True:
			print(f"Fetching page {page}")
			new_events = get_events(page)
			if len(new_events) == 0:
				break
			event_ids = [e["event_index"] for e in new_events]
			params = get_params(event_ids)
			for event, param in zip(new_events, params):
				event["params"] = param["params"]
			events.extend(new_events)
			page += 1
		return events

	events = get_proxy_created_events()
	print(len(events))

	with open(OUT_FILE, "w") as f:
		json.dump(events, f, indent=4)
		print(f"Wrote {len(events)} events to {OUT_FILE}")

# Print all that have a proxy type of other than 'Any'
print(f'Total pure proxies ever created: {len(events)}')
for event in events:
	for param in event["params"]:
		if param["name"] != "proxy_type":
			continue

		if param["value"] != "Any":
			print(f'Found bad proxy of type: {param["value"]}, account: {event["params"][0]["value"]}')
			break
