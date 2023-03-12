import json
import os

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.pyplot
import matplotlib.dates

from datetime import datetime

path = "relay_chain__block_time_over_7_seconds_2023-03-10T17_40_01.193809Z.json"
datas = json.load(open(path))

# extract the date and time from the data
date = []
diff = []
for data in datas:
	date_string = data["date"]
	try:
		timestamp = datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S.%fZ')
	except ValueError:
		timestamp = datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%SZ')
	#timestamp = matplotlib.dates.date2num(timestamp)
	date.append(timestamp)
	diff.append(data["time_diff_seconds"])

incidents_per_day = {}
# count how many incidents happened per day
for d in date:
	day = matplotlib.dates.date2num(d.date())
	if day not in incidents_per_day:
		incidents_per_day[day] = 1
	else:
		incidents_per_day[day] += 1

# log scale
#plt.yscale('log')
# set title
plt.title("Number of slow blocks per day")
days = list(incidents_per_day.keys())
incidents = list(incidents_per_day.values())
plt.plot_date(days, incidents, linestyle='-', marker='o', markersize=1)
plt.gcf().autofmt_xdate()
plt.show()
