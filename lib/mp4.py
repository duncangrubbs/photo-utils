from datetime import datetime
import struct
from typing import Optional


def get_mp4_timestamps(q_path: str) -> tuple[Optional[datetime], Optional[datetime]]:
    """
    Get the creation and modification datetime from MP4 files.

    Returns
     Tuple containing creation_datetime, modification_datetime
    """

    ATOM_HEADER_SIZE = 8
    # difference between Unix epoch and QuickTime epoch, in seconds
    EPOCH_ADJUSTER = 2082844800

    creation_time = modification_time = None

    # search for moov item
    with open(q_path, "rb") as f:
        while True:
            atom_header = f.read(ATOM_HEADER_SIZE)

            print("FOOOOOO", q_path, atom_header)

            if atom_header[4:8] == b"moov":
                break
            else:
                atom_size = struct.unpack(">I", atom_header[0:4])[0]
                f.seek(atom_size - 8, 1)

        atom_header = f.read(ATOM_HEADER_SIZE)
        if atom_header[4:8] == b"cmov":
            raise RuntimeError("moov atom is compressed")
        elif atom_header[4:8] != b"mvhd":
            raise RuntimeError('expected to find "mvhd" header.')
        else:
            f.seek(4, 1)
            creation_time = struct.unpack(">I", f.read(4))[0] - EPOCH_ADJUSTER
            creation_time = datetime.fromtimestamp(creation_time)
            if creation_time.year < 1990:
                creation_time = None

            modification_time = struct.unpack(">I", f.read(4))[0] - EPOCH_ADJUSTER
            modification_time = datetime.fromtimestamp(modification_time)
            if modification_time.year < 1990:
                modification_time = None

    return creation_time, modification_time
