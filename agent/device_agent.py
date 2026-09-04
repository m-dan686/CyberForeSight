import os
import platform
import socket
import time

import psutil
import requests


SERVER = os.getenv(
    "JARVIS_SERVER_URL",
    "http://localhost:5000/device"
)

INTERVAL = 5


def get_ip():

    try:
        return socket.gethostbyname(
            socket.gethostname()
        )

    except Exception:
        return "UNKNOWN"


def get_device_info():

    return {
        "hostname": socket.gethostname(),

        "ip": get_ip(),

        "os": platform.system(),

        "cpu": psutil.cpu_percent(
            interval=1
        ),

        "ram": psutil.virtual_memory().percent,

        "status": "ONLINE"
    }


def send_telemetry():

    data = get_device_info()

    print(
        "\nJARVIS DEVICE TELEMETRY"
    )

    print(
        "========================"
    )

    print(
        "Device:",
        data["hostname"]
    )

    print(
        "IP:",
        data["ip"]
    )

    print(
        "OS:",
        data["os"]
    )

    print(
        "CPU:",
        data["cpu"],
        "%"
    )

    print(
        "RAM:",
        data["ram"],
        "%"
    )

    try:

        response = requests.post(
            SERVER,
            json=data,
            timeout=5
        )

        if response.ok:

            print(
                "Status: SENT"
            )

        else:

            print(
                "Status: SERVER ERROR",
                response.status_code
            )

    except Exception as error:

        print(
            "Status: CONNECTION ERROR",
            error
        )


while True:

    send_telemetry()

    time.sleep(INTERVAL)