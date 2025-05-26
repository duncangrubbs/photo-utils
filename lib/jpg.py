"""UNDER CONSTRUCTION"""

import re
from datetime import datetime


def get_jfif_app0_segment(q_path: str):
    with open(q_path, "rb") as f:
        data = f.read()

    i = 0
    while i < len(data):
        if data[i] == 0xFF:
            print("====", data[i + 1] == 0xE0)
        if data[i] == 0xFF and data[i + 1] == 0xE0:  # APP0 marker
            length = int.from_bytes(data[i + 2 : i + 4], "big")
            segment_data = data[i + 4 : i + 2 + length]

            if segment_data.startswith(b"JFIF\0"):
                return segment_data

        i += 1

    return None


def get_jpg_timestamp(q_path: str) -> datetime | None:
    with open(q_path, "rb") as f:
        data = f.read()

    date_patterns = [
        rb"\d{4}[:\-]\d{2}[:\-]\d{2} \d{2}:\d{2}:\d{2}",
        rb"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
    ]

    for pattern in date_patterns:
        matches = re.findall(pattern, data)
        if matches:
            datestring = matches[0].decode("utf-8")

            datetime.strptime(datestring, "%Y-%m-%dThh:mm:ss")

    return None
