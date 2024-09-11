import yaml
import base64
import os
import requests, sys
import json, csv
from docopt import docopt
from datetime import datetime
from hurry.filesize import alternative, size
from prettytable import PrettyTable

requests.packages.urllib3.disable_warnings()

"""
    This version lets the user specify the aggregate's name then prints the 
        specific data from the aggregate
"""
__program__ = 'Snap_aggr3'
__version__ = 'Version 1'
__revision__ = 'Initial program'



sys.path.append('/home/storagetools')
from mods.common.vault.ver2.vault import Vault

vpath = 'it-storage/KVv1/netapp/common/napi_admin_user'
hashes = Vault(vpath).get_secret()

def args():
    usage = """
    Usage:
      snap_aggr.py <storage> <aggr>
      snap_aggr.py --version
      snap_aggr.py (-h | --help)

    Options:
      -h --help     Show this help message and exit.
    """
    version = '{} VER: {} REV: {}'.format(__program__, __version__, __revision__)
    args = docopt(usage, version=version)
    return args

def Headers():
	username = hashes['Data']['username']
	password = hashes['Data']['password']
	userpass = username + ':' + password
	encoded_u = base64.b64encode(userpass.encode()).decode()

	headers = {"Authorization" : "Basic %s" % encoded_u}

	return headers



def to_json(filename, data):
    json_file_path = f'{filename}/{filename}.json'
    with open(json_file_path, "w") as file:
        json.dump(data, file, indent=2)

def to_txt(filename, table1, table2):
    filename = f'{filename}/{filename}.txt'
    with open(filename, 'w') as file:
        # Write the string representation of the first table to the file
        file.write("Table 1:\n")
        file.write(str(table1))
        file.write("\n\n")
        
        # Write the string representation of the second table to the file
        file.write("Table 2:\n")
        file.write(str(table2))

def to_csv(filename, data):
    csv_file_path = f'{filename}/{filename}.csv'
    with open(csv_file_path, 'w', newline='') as csvfile:
        csv_writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
        csv_writer.writeheader()
        csv_writer.writerows(data)

def calculate_used_percentage(size, used):
    return round(((used / size) * 100), 2)

def aggr_data(storage,vol_data, href):
    url = f"https://{storage}{href}"
    headers = Headers()

    size_rows = []
    available_rows = []
    used_rows = []
    try:
        resp = requests.get(url, verify=False, headers=headers)
        resp = resp.json()
        # Create PrettyTable instance
        table_data = []
        # table.field_names = ["Vserver", "UUID", "BlockStorageSize", "Available", "Used", "PhysicalUsed", "VolumeDeduplicationSpaceSaved"]
        for i in vol_data:
            url_vol = f"https://{storage}/api/storage/volumes/{i['uuid']}"
            vol_data_resp = requests.get(url_vol, verify=False, headers=headers)
            vol_data_resp = vol_data_resp.json()

            size_rows.append(vol_data_resp['space']['size'])
            available_rows.append(vol_data_resp['space']['available'])
            used_rows.append(vol_data_resp['space']['used'],)
            table_data.append({
                "Vserver" : vol_data_resp['svm']['name'],
                "Volume": vol_data_resp['name'],
                "Aggregate": vol_data_resp['aggregates'][0]['name'],
                "State": vol_data_resp['state'],
                "Type": vol_data_resp['type'],
                "Size": size(vol_data_resp['space']['size'], system=alternative),
                "Available": size(vol_data_resp['space']['available'],system=alternative),
                "Used": f"{size(vol_data_resp['space']['used'], system=alternative)}",
                "Used%": f"{calculate_used_percentage(vol_data_resp['space']['size'], vol_data_resp['space']['used'])}%",
                "VolumeSize%" :  f"{calculate_used_percentage(resp['space']['block_storage']['size'], vol_data_resp['space']['size'])}%",
                "VolumeAvailble%" :  f"{calculate_used_percentage(resp['space']['block_storage']['size'], vol_data_resp['space']['available'])}%",
                "VolumeUsed%" :  f"{calculate_used_percentage(resp['space']['block_storage']['size'], vol_data_resp['space']['used'])}%",
                "Is Over-provisoned" :  f"{True if {vol_data_resp['space']['used']} > {vol_data_resp['space']['size']} else False}",


            })


        table = PrettyTable(table_data[0].keys())
        for row in table_data:
            table.add_row(row.values())
        print(table)


        table_sum = PrettyTable()
        table_sum.field_names = ["", "size"]
        table_sum.add_row(["Total Aggr size  ",size(resp['space']["block_storage"]["size"], system=alternative)])
        table_sum.add_row(["Total Aggr size available ",size(resp['space']["block_storage"]["available"], system=alternative)])
        table_sum.add_row(["Total Aggr size  used ",size(resp['space']["block_storage"]["used"], system=alternative)])
        table_sum.add_row(["Total Aggr size  PhysicalUsed ",size(resp['space']["block_storage"]["physical_used"], system=alternative)])
        table_sum.add_row(["Allocated size of all volumes", size(sum(size_rows), system=alternative)])
        table_sum.add_row(["Total sum of all volumes used ", size(sum(used_rows), system=alternative)])



        print(table_sum)
        # Get current date and time
        # now = datetime.now()

        # Format date and time
        # formatted_date_time = now.strftime("%m%d%y_%H%M")
        fl = f"{vol_data_resp['aggregates'][0]['name']}"
        directory = f'{fl}'
        os.makedirs(directory, exist_ok=True)

        to_json(fl, table_data)
        to_csv(fl, table_data)
        to_txt(fl, table,table_sum )

    except Exception as err:
        print(f"Error!: {err}")

def get_aggr(storage, aggr_name):
    agg_url = f"https://{storage}/api/storage/aggregates?name={aggr_name}"
    vol_url = f"https://{storage}/api/storage/volumes?aggregates.name={aggr_name}"

    headers = Headers()

    try:
        resp_aggr = requests.get(agg_url, verify=False, headers=headers)
        resp_vol = requests.get(vol_url, verify=False, headers=headers)

        resp_aggr = resp_aggr.json()
        resp_vol = resp_vol.json()


        if len(resp_aggr['records']) == 0:
            print('Aggregate not found!')
            exit(1)
        aggr_data(storage, resp_vol['records'], resp_aggr['records'][0]['_links']['self']['href'])


    except Exception as err:
        if resp_aggr['error']:
            print(f"Error message: {resp_aggr['error']['message'].upper()}")
            exit(1)
        print(f"Error!: {err}")


def main(args):
    storage = args['<storage>']
    aggr_name = args['<aggr>']

    get_aggr(storage, aggr_name)


if __name__ == '__main__':
    try:
        # Get args from docopt
        arguments = args()

        # with open('config.yaml', 'r') as file:
        #     settings = yaml.safe_load(file)
        
        # uname = settings['username']
        # passwrd = settings['password']
        main(arguments)

    except Exception as err:
        print(f'Error! : {err}')
