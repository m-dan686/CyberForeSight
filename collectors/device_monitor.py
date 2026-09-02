import psutil
import csv
from datetime import datetime

previous = psutil.net_io_counters()

with open("data/device_telemetry.csv", "w", newline="") as file:
    writer = csv.writer(file)

    writer.writerow([
        "timestamp",
        "cpu_percent",
        "memory_percent",
        "bytes_sent_per_sec",
        "bytes_received_per_sec",
        "packets_sent_per_sec",
        "packets_received_per_sec"
    ])

    while True:
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory().percent

        current = psutil.net_io_counters()

        bytes_sent = current.bytes_sent - previous.bytes_sent
        bytes_received = current.bytes_recv - previous.bytes_recv

        packets_sent = current.packets_sent - previous.packets_sent
        packets_received = current.packets_recv - previous.packets_recv

        timestamp = datetime.now()

        writer.writerow([
            timestamp,
            cpu,
            memory,
            bytes_sent,
            bytes_received,
            packets_sent,
            packets_received
        ])

        file.flush()

        print(
            timestamp,
            "| CPU:", cpu, "%",
            "| RAM:", memory, "%",
            "| Sent:", bytes_sent,
            "| Received:", bytes_received
        )

        previous = current