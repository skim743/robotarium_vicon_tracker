sudo docker run -d \
	--net=host \
	--restart unless-stopped \
	-v ~/git/robotarium_nodes_docker/services/vicon_tracker/config/node_desc_tracker.json:/code/descriptor/desc.json \
	-v ~/git/robotarium_nodes_docker/services/vicon_tracker/tracker_node.py:/code/tracker_node.py \
	robotarium:vicon_tracker python3 /code/tracker_node.py -host 192.168.1.5 -port 1884 -interval 33 /code/descriptor/desc.json
