import json
import argparse
import os


def api_node_template(robot_ids):

    link_value = \
        {
            'type': 'STREAM'
        }

    api_node_descriptor = \
        {
            'end_point': 'overhead_tracker',
            'links': {
                    '/all_robot_pose_data': {'type': 'STREAM'} 
                },
            'requests': []
        }

    for r in robot_ids:
        api_node_descriptor['requests'].append({r + '/status': 'optional'})

    return api_node_descriptor


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('mac_config', help='MAC configuration file')
    parser.add_argument('-out_dir', help='The folder to which the descriptor data is written', default='.')

    args = parser.parse_args()
    try:
        f = open(args.mac_config, 'r')
        mac_config = json.load(f)
        f.close()
    except Exception as e:
        print(repr(e))
        print('Could not open given file ({})'.format(args.mac_config))
        return -1

    # Get path of this script and then create directory path to UDP descriptors
    out_path = os.path.abspath(args.out_dir)

    # Make required directories
    if not os.path.exists(out_path):
        os.makedirs(out_path)

    # script_file_name = script_current_directory + "run.sh"
    api_descriptor_file_name = os.path.join(out_path, 'node_desc_api.json')

    # Values of MAC config mapping are the IDs of the robots.
    robot_ids = list(mac_config.values())

    # Generate matlab api descriptor
    try:
        f = open(api_descriptor_file_name, 'w+')
        json.dump(api_node_template(robot_ids), f, sort_keys=True, indent=4, separators=(',', ': '))
        f.close()
    except Exception as e:
        print(repr(e))
        print('Could not open file ({})'.format(api_descriptor_file_name))
        return -1


if __name__ == "__main__":
    main()
