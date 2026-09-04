import requests


SERVER = "http://10.157.15.170:5000/security-event"


def send_event(device, attack, risk, level, action):

    event = {
        "device": device,
        "attack": attack,
        "risk": risk,
        "level": level,
        "action": action
    }

    try:

        response = requests.post(
            SERVER,
            json=event,
            timeout=300
        )

        print("Security event sent:")
        print(event)

        if response.ok:
            print("Status: SENT")
            print("JARVIS response:")
            print(response.json())

        else:
            print(
                "Status: ERROR",
                response.status_code
            )
            print(response.text)

    except Exception as error:

        print(
            "Connection error:",
            error
        )


if __name__ == "__main__":

    send_event(
        device="PC-01",
        attack="PortScan",
        risk=80,
        level="CRITICAL",
        action="MONITOR"
    )