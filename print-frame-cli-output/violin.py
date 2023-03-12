import sys
import os
import json

import numpy as np
import matplotlib.pyplot as plt

def extract_calls(path):
	with open(path, "r") as file:
		data = file.read()
		data = json.loads(data) 
	calls = {}
	for call in data:
		name = call["benchmark"]
		data = [x["extrinsic_time"] / 1000 for x in call["time_results"]]
		calls[name] = data
	return calls

def plot_calls(calls):
	print("Found " + str(len(calls)) + " calls")
	# sort by name
	items = list(calls.items())
	score = {}

	for name, datas in items:
		compos = []
		for data in datas:
			# Calculate linear fitting for data
			x = np.linspace(0, len(data), len(data))
			z = np.polyfit(x, data, 1)
			p = np.poly1d(z)

			compos.append(z[0])
		# score by relative std
		score[name] = np.std(compos) / np.mean(compos)
	# sort by score
	items = sorted(items, key=lambda x: score[x[0]], reverse=True)

	i = 0
	c = 4
	l = 4
	#c = 3
	#l = 3
	fig, axs = plt.subplots(nrows=l, ncols=c)
	fig.suptitle("pallet_contracts --steps=50 --repeats=20 on the last 10 master commits")
	plt.rcParams['axes.titley'] = 1.0
	plt.rcParams['axes.titlepad'] = -10

	for name, datas in items:
		if i >= c * l:
			break
		
		for data in datas:
			# Calculate linear fitting for data
			x = np.linspace(0, len(data), len(data))
			z = np.polyfit(x, data, 1)
			p = np.poly1d(z)

			axs[i // c, i % c].plot(x, p(x), "r--")
			axs[i // c, i % c].set_title(name, fontsize=8)
		i += 1

	for ax in axs.flat:
		ax.set_yticklabels([])
		ax.set_xticklabels([])

	# push the plots together
	fig.tight_layout()
	# remove h spacing
	fig.subplots_adjust(wspace=0.0)
	fig.subplots_adjust(hspace=0.0)
	# remove the margins
	fig.subplots_adjust(left=0.02, right=0.98, top=0.96, bottom=0.03)
	# save as svg
	plt.show()

def main():
	all_calls = {}

	for i in range(1, len(sys.argv)):
		arg = sys.argv[i]
		# Check if a dir and descend recursively
		if os.path.isdir(arg):
			for root, dirs, files in os.walk(arg):
				for file in files:
					if file.endswith(".json"):
						calls = extract_calls(os.path.join(root, file))	
						for name, call in calls.items():
							if name not in all_calls:
								all_calls[name] = []
							all_calls[name].append(call)
		else:
			calls = extract_calls(arg)
			for name, call in calls.items():
				if name not in all_calls:
					all_calls[name] = []
				all_calls[name].append(call)
	
	#plt.ylabel('Time [µs]')
	# log scale
	plot_calls(all_calls)

if __name__ == "__main__":
	main()
