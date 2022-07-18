import os
import re
import sys
import time
import threading
import subprocess
from influxdb import InfluxDBClient

SPEEDTEST_HOST = 'google.com' if not os.environ.get('SPEEDTEST_HOST') else os.environ.get('SPEEDTEST_HOST')
SPEEDTEST_SERVER = 'google.com' if not os.environ.get('SPEEDTEST_SERVER') else os.environ.get('SPEEDTEST_SERVER')
INFLUXDB_DB = 'speedtest' if not os.environ.get('INFLUXDB_DB') else os.environ.get('INFLUXDB_DB')
INFLUXDB_HOST = 'influxdb' if not os.environ.get('INFLUXDB_HOST') else os.environ.get('INFLUXDB_HOST')
INFLUXDB_DB_PORT = 8086 if not os.environ.get('INFLUXDB_DB_PORT') else os.environ.get('INFLUXDB_DB_PORT')
INFLUXDB_USERNAME = 'root' if not os.environ.get('INFLUXDB_USERNAME') else os.environ.get('INFLUXDB_USERNAME')
INFLUXDB_PASSWORD = 'root' if not os.environ.get('INFLUXDB_PASSWORD') else os.environ.get('INFLUXDB_PASSWORD')
SPEEDTEST_INTERVAL = 10 if not os.environ.get('SPEEDTEST_INTERVAL') else os.environ.get('SPEEDTEST_INTERVAL')
SPEEDTEST_HOST_PING = 'google.com' if not os.environ.get('SPEEDTEST_HOST_PING') else os.environ.get('SPEEDTEST_HOST_PING')
SPEEDTEST_HOST_IPERF = 'google.com' if not os.environ.get('SPEEDTEST_HOST_IPERF') else os.environ.get('SPEEDTEST_HOST_IPERF')
iperf_stdout_output = 'iperf_stdout.txt'
ping_stdout_output = 'ping_stdout.txt'
IPERF_INTERVAL = 10 if not os.environ.get('IPERF_INTERVAL') else os.environ.get('IPERF_INTERVAL')

#[{'measurement': 'upload', 'tags': {'host': 'google.com'}, 'fields': {'value': 0.0}}, {'measurement': 'download', 'tags': {'host': 'google.com'}, 'fields':  {'value': 0.0}}, {'measurement': 'ping', 'tags': {'host': 'google.com'}, 'fields':  {'value': 0.0}}]

def push_to_influx(data):
    print("Connecting to db")
    client = InfluxDBClient(host=INFLUXDB_HOST, 
    username=INFLUXDB_USERNAME,
    password=INFLUXDB_PASSWORD,
    port=INFLUXDB_DB_PORT)
    data_p = []
    for k, v in data.items():
        data_p.append({'measurement': k, 'tags': {'host': SPEEDTEST_HOST_IPERF}, 'fields': {'value': v}})
    print(data_p)
    client.switch_database(INFLUXDB_DB)
    client.write_points(data_p)

def process_iperf_data():
    print("Processing iperf data")
    patt_iperf = r'\d+[.0-9]\d+ [MG]Bytes'
    patt_ping = r'time=\d+[.]\d+'
    upload = download = latency = 0.0
    with open(ping_stdout_output) as f:
        ping_data = f.read()

    with open(iperf_stdout_output) as f:
        iperf_data = f.read()
    print("iPerf Data:")
    print(iperf_data)
    print("Ping Data")
    print(ping_data)
    latency = re.findall(patt_ping, ping_data)
    vals = re.findall(patt_iperf, iperf_data)
    if latency:
        for i,j in enumerate(latency):
            latency[i] = float(j.split('time=')[1])
        latency = sum(latency) / len(latency)
    print(vals)
    if vals:
       
        speed = vals[-1]
        if 'GB' in speed:
            speed = float(speed.split()[0]) * 1024 / IPERF_INTERVAL
        elif 'MB' in speed:
            speed = float(speed.split()[0]) / IPERF_INTERVAL
        else:
            print("Error parsing iperf data")
            time.sleep(5)
            sys.exit(2)
    download = upload = speed  
    print(f"Download speed is {download}")
    
    return upload, download, latency


def fork(command, args=None):

    res=subprocess.run(
    command, shell=True, encoding='utf-8', stdout=subprocess.PIPE,
    stderr=subprocess.PIPE)
    return res.returncode, res.stdout, res.stderr


def start_speedtest():
    
    while True:
        s_file = str(time.time() * 100)
        server_ping = SPEEDTEST_HOST_PING
        server_iperf = SPEEDTEST_HOST_IPERF
        iperf_cmd = ["iperf -c {} -i 1 -p 5012 -b 800m -l1200  -t {} -u -y > {}".format(
            server_iperf, IPERF_INTERVAL, iperf_stdout_output
        )]
        ping_cmd = ["ping -c 20 {} > {}".format(
            server_ping, ping_stdout_output
        )]
        iperf_return_code, iperf_stdout, iperf_stderr = fork(iperf_cmd)
        ping_return_code, ping_stdout, ping_stderr = fork(ping_cmd)
        if ping_return_code == 0:
            ul, dl, lt = process_iperf_data()

            speed_metrics = {
                'upload': ul,
                'download': dl,
                'ping': lt
            }
            print("Speed metrics: ")
            print(speed_metrics)

            try:
                push_to_influx(speed_metrics)
                print("INFLUX DB data updated")
            except Exception as e:
                print(f'Failed to update Influx DB {e}')
                time.sleep(5)
        else:
            print("Failed to run command correctly")
            print(iperf_stderr)
            print(ping_stderr)

        #time.sleep(SPEEDTEST_INTERVAL)

if __name__ == '__main__':
    start_speedtest()
    printf("Speedtest stopped...")


