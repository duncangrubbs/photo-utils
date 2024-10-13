import os
from datetime import datetime
import random
from collections import defaultdict
import time
from typing import Optional
from exif import Image
from tqdm import tqdm


class Utils:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir

    def get_clean_file_list(self):
        return [
            os.path.join(self.base_dir, x)
            for x in os.listdir(self.base_dir)
            if x not in [".DS_Store"]
        ]

    def get_extension(self, q_path: str) -> str:
        return q_path.split(".")[-1].lower()

    def get_metadata(
        self, q_path: str, valid_extentions: list[str] = ["jpg"]
    ) -> Optional[Image]:
        if self.get_extension(q_path) not in valid_extentions:
            return

        with open(q_path, "rb") as image_file:
            return Image(image_file)

    def update_dates_from_metadata(self):
        for q_path in tqdm(self.get_clean_file_list()):
            metadata = self.get_metadata(q_path)
            ext = self.get_extension(q_path=q_path)
            if metadata is None:
                continue

            try:
                parsed_datetime = datetime.strptime(
                    metadata.datetime, "%Y:%m:%d %H:%M:%S"
                )
                correct_file_name = self.build_file_datestring(parsed_datetime, ext)
                if correct_file_name in q_path.split("/")[-1].split("R")[0]:
                    continue

                unixtime = time.mktime(parsed_datetime.timetuple())
                os.utime(q_path, (unixtime, unixtime))
                os.rename(
                    q_path,
                    os.path.join(
                        self.base_dir, self.build_file_datestring(parsed_datetime, ext)
                    ),
                )
            except Exception as e:
                print(e)
                continue

    def build_file_datestring(self, dt: datetime, ext: str) -> str:
        return f"{dt.strftime("%Y-%m-%dT%H-%M-%S")}R{random.randint(1000, 9999)}.{ext}"

    def convert_names_to_dates(self):
        for q_path in self.get_clean_file_list():
            dt = datetime.fromtimestamp(os.path.getmtime(q_path))
            ext = self.get_extension(q_path)
            os.rename(
                q_path,
                os.path.join(self.base_dir, self.build_file_datestring(dt, ext)),
            )

    def find_duplicates(self):
        duplicates = defaultdict(lambda: [])
        for q_path in self.get_clean_file_list():
            a, b = q_path.split("R")

            key = f"{a}_{q_path.split(".")[-1]}"
            if len(duplicates[key]) == 1:
                print(a)
            duplicates[key].append(b)
