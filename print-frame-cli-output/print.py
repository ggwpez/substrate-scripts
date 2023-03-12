import sys
import os
import json

import numpy as np
import matplotlib.pyplot as plt

def plot(path, linear=True):
	with open(path, "r") as file:
		data = file.read()
		data = json.loads(data) 
	
	data = data[0]
	name = data["pallet"] + "::" + data["benchmark"]

	# Extract the extrinsic_time of the time_results
	time = [x["extrinsic_time"] / 1000 for x in data["time_results"]]
	# Print the averages

	# Print a linear fitting if desired
	if linear:
		# Linear fitting
		x = np.linspace(0, len(time), len(time))
		z = np.polyfit(x, time, 1)
		p = np.poly1d(z)
		# Print the linear equation
		print(name + " = " + str(z[0]) + " * x + " + str(z[1]))
		plt.plot(x, p(x), label="fitting", color="red", zorder=1000, alpha=0.5)

	# print the 100 value moving average
	time = np.convolve(time, np.ones((100,))/100, mode='valid')
	# indicate their average at the left side
	#plt.axhline(y=np.mean(time), color='r', linestyle='-', alpha=0.5, zorder=1000)

	# Plot the data
	file_name = os.path.basename(path)
	#print(path)
	plt.plot(time, label=file_name, alpha=0.5)
	plt.title("Last 10 master commits, 10 times 2000 repeats of " + name + " (moving average n=100)")

def main():
	for i in range(1, len(sys.argv)):
		arg = sys.argv[i]
		# Check if a dir and descend recursively
		if os.path.isdir(arg):
			for root, dirs, files in os.walk(arg):
				for file in files:
					if file.endswith(".json"):
						plot(os.path.join(root, file))	
		else:
			plot(arg)

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
	#plt.legend()
	plt.tight_layout()
	plt.show()

if __name__ == "__main__":
	main()
