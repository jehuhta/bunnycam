import os

path = r"/media/jessurpi/ESD-USB/Bunnycam_frame_predictions"
devices = ["E8F60A870078"]


filtered_dir = []
for device in devices:
	for file in os.listdir(path):
		if device in file and file.endswith(".jpg"):
			filtered_dir.append(file)
			 
print(filtered_dir[-1])
