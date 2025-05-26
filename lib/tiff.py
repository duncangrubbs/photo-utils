"""UNDER CONSTRUCTION"""

import struct


def get_tiff_timestamp(q_path: str):
    with open(q_path, "rb") as f:
        header = f.read(8)
        print(header)

        # Detect byte order (II = Intel / little-endian, MM = Motorola / big-endian)
        byte_order = header[0:2]
        endian = "<" if byte_order == b"II" else ">"

        # Confirm TIFF format (should be 42 as uint16)
        tiff_id = struct.unpack(endian + "H", header[2:4])[0]
        print(tiff_id)
        if tiff_id != 42:
            raise ValueError("Not a valid TIFF file.")

        # Offset to first IFD (Image File Directory)
        ifd_offset = struct.unpack(endian + "I", header[4:8])[0]
        f.seek(ifd_offset)

        # Number of directory entries
        num_entries = struct.unpack(endian + "H", f.read(2))[0]
        print(num_entries)

        for _ in range(num_entries):
            entry = f.read(12)
            print(entry)
            tag, type_, count, value_offset = struct.unpack(endian + "HHII", entry)
            print(tag)
            if tag == 0x0132:  # DateTime tag
                print(tag)
                if type_ == 2:  # ASCII
                    f.seek(value_offset)
                    datetime_str = f.read(count).split(b"\x00")[0].decode("ascii")
                    print(datetime_str)
                    return None
                    return datetime_str

        return None
