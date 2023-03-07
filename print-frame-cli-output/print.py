import sys
import os
import json

import numpy as np
import matplotlib.pyplot as plt

def plot(path):
	with open(path, "r") as file:
		data = file.read()
		data = json.loads(data) 

	data = data[0]
	name = data["pallet"] + "::" + data["benchmark"]

	# Extract the extrinsic_time of the time_results
	time = [x["extrinsic_time"] / 1000 for x in data["time_results"]]

	# Print the averages
	print(f'Average of {name}: {np.mean(time)}')

	# Plot the data
	file_name = os.path.basename(path)
	plt.plot(time, label=file_name, alpha=0.5)
	plt.title(name)

def main():
	first = sys.argv[1]
	# Check if a dir
	if os.path.isdir(first):
		# Iterate over all files in the dir
		for file in os.listdir(first):
			# Check if json
			if file.endswith(".json"):
				# Plot the file
				plot(os.path.join(first, file))
	else:
		for i in range(1, len(sys.argv)):
			plot(sys.argv[i])

	# Also plot the equation 12.57 + 4.839 * x
	#x = np.linspace(0, 10000, 10000)
	#y = 0.4839 * x
	#plt.plot(x, y, label="fitting offset=0", color="red")
	#y = 30 + 0.4839 * x
	#plt.plot(x, y, label="fitting offset=30", color="red")

	# Y axis is microseconds
	plt.ylabel('Time [µs]')
	# log y
	#plt.yscale('log')
	plt.legend()
	plt.show()

if __name__ == "__main__":
	main()
