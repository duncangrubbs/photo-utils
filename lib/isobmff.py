from datetime import datetime
import struct


def get_isobmff_timestamp(
    q_path: str,
) -> datetime | None:
    """
    Get the creation and modification datetime from isobmff files.

    Returns
        creation_datetime of the image
    """

    ATOM_HEADER_SIZE_BYTES = 8
    # difference between Unix epoch and QuickTime epoch, in seconds
    EPOCH_ADJUSTER = 2082844800

    creation_time = None

    # search for moov item
    with open(q_path, "rb") as f:
        while True:
            atom_header: bytes = f.read(ATOM_HEADER_SIZE_BYTES)
            if atom_header[4:8] == b"moov":
                break
            else:
                atom_size = struct.unpack(">I", atom_header[0:4])[0]
                if atom_size == 1:
                    extended_size: bytes = f.read(
                        ATOM_HEADER_SIZE_BYTES
                    )  # read 64 bit extended size
                    atom_size = struct.unpack(">Q", extended_size)[0]
                    f.seek(atom_size - 16, 1)  # we are now 16 bytes into this
                else:
                    f.seek(atom_size - 8, 1)

        atom_header = f.read(ATOM_HEADER_SIZE_BYTES)
        if atom_header[4:8] == b"cmov" or atom_header[4:8] != b"mvhd":
            return None
        else:
            f.seek(4, 1)
            creation_time = struct.unpack(">I", f.read(4))[0] - EPOCH_ADJUSTER
            creation_time = datetime.fromtimestamp(creation_time)
            if creation_time.year < 1990:
                creation_time = None

    return creation_time
