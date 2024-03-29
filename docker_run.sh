sudo docker run -d \
	--net=host \
	--restart=always \
	--name=robotarium_vicon_tracker \
	-v ~/git/robotarium_vicon_tracker/config/node_desc_tracker.json:/code/descriptor/desc.json \
	-v ~/git/robotarium_vicon_tracker/tracker_node.py:/code/tracker_node.py \
	robotarium:vicon_tracker python3 /code/tracker_node.py -host 192.168.1.8 -port 1884 -tracker_host 192.168.10.1 -interval 33 /code/descriptor/desc.json
