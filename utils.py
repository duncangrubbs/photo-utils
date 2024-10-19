from enum import StrEnum
import os
from datetime import datetime
import random
from collections import defaultdict
import time
from typing import Optional
from exif import Image
import filetype
from logger import get_logger

logger = get_logger()


class FileExtensions(StrEnum):
    JPG = "jpg"
    NEF = "nef"
    JPEG = "jpeg"
    PNG = "png"
    HEIC = "heic"
    MOV = "mov"
    MP4 = "mp4"


EXCLUDED_FILES = [".DS_Store"]


class Utils:
    def __init__(self, base_dir: str, is_dry_run: bool = False):
        self.base_dir = base_dir
        self.is_dry_run = is_dry_run
        self.log = logger.bind(is_dry_run=self.is_dry_run)
        if self.is_dry_run:
            self.log.info("Running in dry-run mode.")
        else:
            self.log.warning("Running in live mode.")

    def get_clean_file_list(self):
        """Returns the fully qualified path of all files in the base directory."""
        return [
            os.path.join(self.base_dir, x)
            for x in os.listdir(self.base_dir)
            if x not in EXCLUDED_FILES
        ]

    def get_extension(self, q_path: str) -> str:
        """Given a qualified path of a file, this returns the extension of the file."""
        return os.path.splitext(q_path)[1].replace(".", "").lower()

    def strip_extension(self, q_path: str) -> str:
        """Given a qualified path of a file, this returns everything but the extension."""
        return os.path.splitext(q_path)[0]

    def get_file_type(self, q_path: str) -> str:
        """
        Given a qualified path of a file, this returns the best guess actual
        file type extension based on the header data.
        """
        return filetype.guess(q_path).extension.lower()

    def _rename(self, src: str, dst: str):
        """
        Renames a file from src to dst. If dry-run mode is enabled, it will log instead
        """
        if self.is_dry_run:
            self.log.info(f"Would rename {src} to {dst}")
            return
        self.log.info("Rename", src=src, dst=dst)
        os.rename(src, dst)

    def _utime(
        self,
        path: str,
        times: tuple[int, int] | tuple[float, float] | None = None,
    ):
        """
        Wrap the os.utime function to allow for dry-run mode.
        """
        if self.is_dry_run:
            self.log.info(f"Would update time for {path}", times)
            return
        self.log.info("Updating time for", path, times)
        os.utime(path, times)

    def correct_file_types(self):
        """
        Corrects the file extensions based on the actual file type from the header data.
        If dry-run mode is enabled, it will log instead.
        """
        for file in self.get_clean_file_list():
            real_ext = self.get_file_type(file)
            curr_ext = self.get_extension(file)
            if curr_ext == FileExtensions.NEF or curr_ext == FileExtensions.MOV:
                continue
            if real_ext != curr_ext:
                self._rename(
                    file,
                    os.path.join(
                        self.base_dir, f"{self.strip_extension(file)}.{real_ext}"
                    ),
                )

    def get_file_created_date(
        self,
        q_path: str,
    ) -> Optional[datetime]:
        """
        Pulls the created at date from the EXIF data of the file.
        If the file doesn't have EXIF data, it will return None.
        """
        if self.get_extension(q_path) in [
            FileExtensions.JPG,
            FileExtensions.JPEG,
        ]:
            try:
                with open(q_path, "rb") as image_file:
                    metadata = Image(image_file)
                    return datetime.strptime(metadata.datetime, "%Y:%m:%d %H:%M:%S")
            except Exception as e:
                logger.info("Failed to get metadata for", q_path, e)
                return None
        return None

    def update_dates_from_metadata(self):
        for q_path in self.get_clean_file_list():
            metadata = self.get_file_created_date(q_path)
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

                self._utime(q_path, (unixtime, unixtime))
                self._rename(
                    q_path,
                    os.path.join(
                        self.base_dir,
                        self.build_file_datestring(parsed_datetime, ext),
                    ),
                )
            except Exception:
                self.log.exception("Failed to update", q_path=q_path)
                continue

    def build_file_datestring(self, dt: datetime, ext: str) -> str:
        """
        Given a datetime and an extension, this returns a formatted string in the standard
        file format for this project.

        This format is as follows:
        YYYY-MM-DDTHH-MM-SSRXXXX.EXT
        In which XXXX is a random number between 1000 and 9999 to avoid name clashes
        """
        return f"{dt.strftime("%Y-%m-%dT%H-%M-%S")}R{random.randint(1000, 9999)}.{ext}"

    def convert_names_to_dates(self):
        """
        Normalizes filenames in the standard format based on
        the created date for the file
        """
        for q_path in self.get_clean_file_list():
            dt = datetime.fromtimestamp(os.path.getmtime(q_path))
            ext = self.get_extension(q_path)
            self._rename(
                q_path,
                os.path.join(self.base_dir, self.build_file_datestring(dt, ext)),
            )

    def find_duplicates(self):
        """Finds files with duplicate names, excluding the random number."""
        duplicates = defaultdict(lambda: [])
        for q_path in self.get_clean_file_list():
            a, b = q_path.split("R")

            key = f"{a}_{q_path.split(".")[-1]}"
            if len(duplicates[key]) == 1:
                logger.info(a)
            duplicates[key].append(b)
