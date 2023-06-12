sudo docker run -d \
	--net=host \
	--restart=always \
	--name=robotarium_vicon_tracker \
	-v ~/git/vicon_tracker_python/config/node_desc_tracker.json:/code/descriptor/desc.json \
	-v ~/git/vicon_tracker_python/tracker_node.py:/code/tracker_node.py \
	robotarium:vicon_tracker python3 /code/tracker_node.py -host 192.168.1.5 -port 1884 -interval 33 /code/descriptor/desc.json
