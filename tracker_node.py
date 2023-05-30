import time
import json
import argparse
import vizier.node as node
import vrpn
import math
import threading
import concurrent.futures as futures
import logging

global logger
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
logger = logging.getLogger('root')
logger.setLevel(logging.DEBUG)

# Timeout for VRPN data in seconds
timeout = 10

# tracker data dictionary
# Add one to actually include max value
global robot_data
global robot_data_lock
global getting_data
global robots

robot_data = {}
robot_data_lock = threading.Lock()
getting_data = {}
robots = []


def create_vrpn_handler(robot_name):
    """Creates and returns a function that represents a data handler for incoming VRPN data.

    Args:
        robot_name:

    Returns:

    """
    # TODO: Round sent numbers to millimeter or something
    def f(user_data, msg):
        global robot_data
        global getting_data

        # This is going to contain power data for the robot
        with robot_data_lock:
            # Position data is in x y z format
            robot_data[robot_name]['x'] = round(msg['position'][0], 3)
            robot_data[robot_name]['y'] = round(msg['position'][1], 3)
            (qx, qy, qz, qw) = msg['quaternion']

            robot_data[robot_name]['theta'] = round(math.atan2(2.0*(qw*qz + qx*qy), 1.0 - 2.0*(qy*qy + qz*qz)), 3)

            # Set last time we got VRPN data.  Used in timeout detection later
            getting_data[robot_name]['vrpn'] = time.time()

    return f


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("node_descriptor", help=".json file node information")
    parser.add_argument("-port", type=int, help="MQTT Port", default=1884)
    parser.add_argument("-host", help="MQTT Host IP", default="localhost")
    parser.add_argument("-interval", type=int, help="Publishing interval in milliseconds", default=16)

    args = parser.parse_args()

    interval = args.interval/1000

    # Ensure that we can open the nodes file
    node_descriptor = None

    try:
        f = open(args.node_descriptor, 'r')
        node_descriptor = json.load(f)
        f.close()
    except Exception as e:
        print(repr(e))
        print("Couldn't open given node file " + args.node_descriptor)
        return -1

    tracker_node = node.Node(args.host, args.port, node_descriptor)
    try:
        tracker_node.start()
    except Exception as e:
        print(repr(e))
        #print("I'm quitting...")
        quit()

    global robots
    global robot_data
    global robot_data_lock
    global getting_data

    potential_topics = tracker_node.gettable_links
    print('Potential available robots: ', potential_topics)
    robots = list({x.split('/')[0] for x in potential_topics})
    getting_data = dict({r: {'vrpn': time.time(), 'viz': False} for r in robots})
    robot_data = dict({r: {'x': 0, 'y': 0, 'theta': 0} for r in robots})

    executor = futures.ThreadPoolExecutor(max_workers=len(robots))
    running = True

    def get_data_task():
        global robots
        global robot_data
        global robot_data_lock
        global getting_data
        nonlocal executor
        nonlocal running

        links = list([r+'/status' for r in robots])

        while running:
            current_time = time.time()
            data = []
            try:
                data = list(executor.map(lambda x: tracker_node.get(x, timeout=0.5, attempts=4), links, timeout=3))
            except Exception as e:
                print(repr(e))

            for i, d in enumerate(data):
                r = robots[i]
                with robot_data_lock:
                    if d is not None:
                        try:
                            d = json.loads(d)
                            robot_data[r].update(d)
                            getting_data[r]['viz'] = True
                        except Exception as e:
                            getting_data[r]['viz'] = False
                            print(repr(e))
                    else:
                        getting_data[r]['viz'] = False

            print(data)
            # TODO: Make this sleep for at most 2 seconds
            time.sleep(max(0, 2 - (time.time() - current_time)))

    # Start thread to get data for robots
    robot_data_thread = threading.Thread(target=get_data_task)
    robot_data_thread.start()

    # Create all VRPN callbacks for receiving position data
    vrpn_tuples = {x: (vrpn.receiver.Tracker(x+"@192.168.1.4"), create_vrpn_handler(x)) for x in robots}
    for (tracker, tracker_cb) in vrpn_tuples.values():
        tracker.register_change_handler(None, tracker_cb, "position")

    current_time = time.time()

    while True:

        # In this case, we catastrophically delete stuff because Vicon is being
        # weird
        for v in vrpn_tuples:
            #     Call the tracker mainloop
            vrpn_tuples[v][0].mainloop()

        # Prune for active robots
        to_send = {}
        for r in robots:
            if(getting_data[r]['viz'] and (current_time - getting_data[r]['vrpn']) <= timeout):
                to_send[r] = robot_data[r]

        with robot_data_lock:
            # Send only if we don't have an empty message
            if(len(to_send) > 0):
                msg = json.dumps(to_send)
                msg += ''.join(' ' for __ in range(1500 - len(msg)))
                tracker_node.publish('overhead_tracker/all_robot_pose_data', msg)

        if(min([current_time - getting_data[x]['vrpn'] for x in robots]) >= timeout):
            logger.error('All robots timed out.  Exiting.')
            running = False
            tracker_node.stop()
            quit()

        # Wait for the right amount of time
        elapsed_time = time.time() - current_time
        time.sleep(max(0, interval - elapsed_time))

        #print(time.time() - current_time)

        current_time = time.time()


if __name__ == "__main__":
    main()
