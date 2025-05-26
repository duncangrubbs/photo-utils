from enum import StrEnum
from io import BufferedReader
import os
from datetime import datetime
import random
from collections import defaultdict
import time
import filetype
from lib.logger import get_logger
import hashlib
from PIL import Image as PILImage, ExifTags, ImageFile
from pillow_heif import register_heif_opener


from lib.isobmff import get_isobmff_timestamp

logger = get_logger()

DuplicateFileMap = dict[int, list[str]]


class FileExtensions(StrEnum):
    JPG = "jpg"
    NEF = "nef"
    JPEG = "jpeg"
    PNG = "png"
    HEIC = "heic"
    MOV = "mov"
    MP4 = "mp4"
    TIF = "tif"
    TIFF = "tiff"
    GIF = "gif"


EXCLUDED_FILES = [".DS_Store"]
DEFAULT_HASH_CHUNK_SIZE = 1024


class Utils:
    """
    Wrapper class for all the utility functions that are used in the CLI.
    """

    def __init__(self, base_dir: str, is_dry_run: bool = False):
        self.base_dir = base_dir
        register_heif_opener()
        self.is_dry_run = is_dry_run
        self.log = logger.bind(is_dry_run=self.is_dry_run)
        if self.is_dry_run:
            self.log.info("Running in dry-run mode.")
        else:
            self.log.warning("Running in live mode.")

    def get_clean_file_list(self) -> list[str]:
        """Returns the fully qualified path of all files in the base directory."""
        try:
            all_files = [
                os.path.join(self.base_dir, x)
                for x in os.listdir(self.base_dir)
                if x not in EXCLUDED_FILES
            ]
            self.log.info("Found files", count=len(all_files))
            return all_files
        except FileNotFoundError:
            logger.warning("Base path not found", base_dir=self.base_dir)
            return []

    def get_extension(self, q_path: str) -> FileExtensions:
        """Given a qualified path of a file, this returns the extension of the file."""
        extension: str = os.path.splitext(q_path)[1].replace(".", "").lower()
        return FileExtensions(extension)

    def strip_extension(self, q_path: str) -> str:
        """Given a qualified path of a file, this returns everything but the extension."""
        return os.path.splitext(q_path)[0]

    def get_file_type(self, q_path: str) -> FileExtensions:
        """
        Given a qualified path of a file, this returns the best guess actual
        file type extension based on the header data.
        """
        guessed_ext = filetype.guess(q_path)
        if guessed_ext and guessed_ext.extension:
            return FileExtensions(str(guessed_ext.extension).lower())

        self.log.debug("Failed to guess file type", q_path=q_path)
        return self.get_extension(q_path)

    def _rename(self, src: str, dst: str):
        """
        Renames a file from src to dst. If dry-run mode is enabled, it will log instead
        """
        if self.is_dry_run:
            self.log.info("[DRY RUN] Renamed", src=src, dst=dst)
            return
        self.log.info("Renamed", src=src, dst=dst)
        os.rename(src, dst)

    def _utime(
        self,
        path: str,
        times: tuple[int, int] | tuple[float, float] | None = None,
    ):
        """
        Wrap the os.utime function to allow for dry-run mode.
        """
        time = (
            datetime.fromtimestamp(times[0]).strftime("%Y-%m-%d %H:%M:%S")
            if times is not None
            else None
        )
        if self.is_dry_run:
            self.log.info(
                "[DRY RUN] Updating time",
                time=time,
                path=path,
            )
            return
        self.log.info(
            "Updating time",
            path=path,
            time=time,
        )
        os.utime(path, times)

    def make_ext_lowercase(self, file: str):
        curr_ext = self.get_extension(file)
        if curr_ext == os.path.splitext(file)[1].replace(".", ""):
            return

        self._rename(
            file,
            os.path.join(self.base_dir, f"{self.strip_extension(file)}.{curr_ext}"),
        )

    def correct_file_types(self):
        """
        Corrects the file extensions based on the actual file type from the header data.
        If dry-run mode is enabled, it will log instead.
        """
        for file in self.get_clean_file_list():
            real_ext = self.get_file_type(file)
            curr_ext = self.get_extension(file)

            if curr_ext == FileExtensions.NEF or curr_ext == FileExtensions.MOV:
                # for now we can ignore these file types since the library tends to get
                # them wrong
                self.make_ext_lowercase(file)
                continue

            if real_ext != curr_ext:
                self._rename(
                    file,
                    os.path.join(
                        self.base_dir, f"{self.strip_extension(file)}.{real_ext}"
                    ),
                )
            else:
                self.make_ext_lowercase(file)

    def get_datetime_from_image_xml(
        self,
        parsed_file_data: ImageFile.ImageFile,
    ) -> datetime | None:
        """
        Attempts to parse image metadata XML to find a created datetime.
        If it cannot find one, it returns None.
        """
        xml_data = parsed_file_data.info["xmp"].decode("utf-8")
        start_index = xml_data.find("<photoshop:DateCreated>")
        end_index = xml_data.find("</photoshop:DateCreated>")

        if start_index == -1 or end_index == -1:
            return None
        return datetime.fromisoformat(xml_data[start_index + 23 : end_index])

    def get_file_created_date(
        self,
        q_path: str,
    ) -> datetime | None:
        """
        First gets the EXIF data from the file. If there is EXIF data
        and it contains a datetime, it uses that.

        If there isn't EXIF data or if the data doesn't have a datetime
        then it falls back to format specific parsing.

        If that fails it returns None
        """
        try:
            if (
                self.get_extension(q_path) == FileExtensions.MOV
                or self.get_extension(q_path) == FileExtensions.MP4
            ):
                return get_isobmff_timestamp(q_path)

            parsed_file_data = PILImage.open(q_path)

            exif_data_dict = {
                ExifTags.TAGS[k]: v
                for k, v in parsed_file_data.getexif().items()
                if k in ExifTags.TAGS and type(v) is not bytes
            }

            if "DateTime" in exif_data_dict:
                return datetime.strptime(
                    exif_data_dict["DateTime"], "%Y:%m:%d %H:%M:%S"
                )

            return self.get_datetime_from_image_xml(parsed_file_data)
        except Exception as e:
            self.log.warning(
                "Failed to parse image metadata for datetime", q_path=q_path, e=e
            )
            return None

    def update_dates_from_metadata(self):
        """Update the file created date based on the metadata."""
        for q_path in self.get_clean_file_list():
            parsed_datetime = self.get_file_created_date(q_path)
            creation_time = os.path.getmtime(q_path)
            ext = self.get_extension(q_path=q_path)

            if parsed_datetime is None or parsed_datetime == datetime.fromtimestamp(
                creation_time
            ):
                continue

            try:
                correct_file_name = self.build_file_datestring(parsed_datetime, ext)
                if correct_file_name in q_path.split("/")[-1].split("R")[0]:
                    continue

                unixtime = time.mktime(parsed_datetime.timetuple())

                self._utime(q_path, (unixtime, unixtime))
            except Exception:
                self.log.warning("Failed to update", q_path=q_path)
                continue

    def build_file_datestring(
        self, dt: datetime, ext: str, prevent_duplicates: bool = True
    ) -> str:
        """
        Given a datetime and an extension, this returns a formatted string in the standard
        file format for this project.

        This format is as follows:
        YYYY-MM-DDTHH-MM-SSRXXXX.EXT

        In which XXXX is a random number between 1000 and 9999 to avoid name clashes
        """
        formatted_date = dt.strftime("%Y-%m-%dT%H-%M-%S")
        normalized_ext = ext.lower()
        if not prevent_duplicates:
            return f"{formatted_date}.{normalized_ext}"
        return f"{formatted_date}R{random.randint(1000, 9999)}.{normalized_ext}"

    def convert_names_to_dates(self, prevent_duplicates: bool):
        """
        Normalizes filenames in the standard format based on
        the created date for the file
        """
        for q_path in self.get_clean_file_list():
            dt = datetime.fromtimestamp(os.path.getmtime(q_path))
            ext = self.get_extension(q_path)
            new_path = os.path.join(
                self.base_dir,
                self.build_file_datestring(dt, ext, prevent_duplicates),
            )

            # If the file already has the correct name, skip it
            if q_path.split("R")[0] == new_path.split("R")[0]:
                continue

            self._rename(
                q_path,
                new_path,
            )

    def _read_chunks(
        self, file_obj: BufferedReader, chunk_size_bytes: int = DEFAULT_HASH_CHUNK_SIZE
    ):
        """Generator that reads a file in chunks of bytes"""
        while True:
            chunk = file_obj.read(chunk_size_bytes)
            if not chunk:
                return
            yield chunk

    def _get_hash(self, filename: str, first_chunk_only: bool = False) -> bytes:
        """
        Given a file path, return the hash of the file.
        Optionally only hash the first chunk of the file.
        """
        hashobj = hashlib.sha1()
        with open(filename, "rb") as f:
            if first_chunk_only:
                hashobj.update(f.read(DEFAULT_HASH_CHUNK_SIZE))
            else:
                for chunk in self._read_chunks(f):
                    hashobj.update(chunk)
        return hashobj.digest()

    def find_duplicates(self) -> DuplicateFileMap:
        """
        Finds files that are duplicates by hashing their contents

        Returns: a dictionary mapping a file size to a list
        of files names that have that size
        """
        paths = self.get_clean_file_list()
        files_by_size: defaultdict[int, list[str]] = defaultdict(list)
        files_by_small_hash: defaultdict[tuple[int, bytes], list[str]] = defaultdict(
            list
        )
        files_by_full_hash: dict[bytes, str] = dict()

        for path in paths:
            full_path = path
            try:
                # if the target is a symlink (soft one), this will
                # dereference it - change the value to the actual target file
                full_path = os.path.realpath(full_path)
                file_size = os.path.getsize(full_path)
            except OSError:
                # not accessible (permissions, etc) - pass on
                self.log.warning("Insufficient permissions", path=full_path)
                continue
            files_by_size[file_size].append(full_path)

        # For all files with the same file size, get their hash on the first 1024 bytes
        for file_size, files in files_by_size.items():
            if len(files) < 2:
                continue  # this file size is unique, no need to spend cpu cycles on it

            for filename in files:
                try:
                    small_hash = self._get_hash(filename, first_chunk_only=True)
                except OSError:
                    # the file access might've changed till the exec point got here
                    continue
                files_by_small_hash[(file_size, small_hash)].append(filename)

        # For all files with the hash on the first 1024 bytes, get their hash on the full
        # file - collisions will be duplicates
        for files in files_by_small_hash.values():
            if len(files) < 2:
                # the hash of the first 1k bytes is unique -> skip this file
                continue

            for filename in files:
                try:
                    full_hash = self._get_hash(filename, first_chunk_only=False)
                except OSError:
                    # the file access might've changed till the exec point got here
                    continue

                if full_hash in files_by_full_hash:
                    duplicate = files_by_full_hash[full_hash]
                    self.log.info(
                        "Duplicate found", filename=filename, duplicate=duplicate
                    )
                else:
                    files_by_full_hash[full_hash] = filename

        return {
            k: sorted([x.split("/")[-1] for x in v])
            for k, v in files_by_size.items()
            if len(v) > 1
        }
