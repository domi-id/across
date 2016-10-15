#!/usr/bin/env python

import os

from construct import *

from common import ZeroString, FixedArray, test_folder, mkdir_p
from encryption import EncryptedBlock


RES_ENCRYPTION = 23, 9782, 3391, 31

# noinspection PyPep8,PyUnresolvedReferences
ResourceEntry = Struct(
    "name"   / ZeroString(16),
    "offset" / Int32ul,
    "size"   / Int32ul
)

# noinspection PyPep8,PyUnresolvedReferences
RawResourceFile = Struct(
    "files_num"  / Int32ul,
    "file_table" / EncryptedBlock(RES_ENCRYPTION,
                                  FixedArray(150, this.files_num, ResourceEntry)),
    Const(Int32ul, 0x1490ff),
    "raw_data" / GreedyBytes
)


class ResourceFileAdapter(Adapter):
    """
    Discards header and returns a dict of {file_name: file_data}
    """

    HEADER_SIZE = 3608  # 4 + 150 * 24 + 4

    def _decode(self, obj, context):
        shift = self.HEADER_SIZE
        return {f.name: obj.raw_data[f.offset - shift:f.offset + f.size - shift]
                for f in obj.file_table}

    def _encode(self, files, context):
        file_table = []
        raw_data = b""
        last_offset = self.HEADER_SIZE
        for file_name, file_data in files.items():
            file_table.append({"name": file_name,
                               "offset": last_offset,
                               "size": len(file_data)})
            last_offset += len(file_data)
            raw_data += file_data

        return {"files_num": len(files),
                "file_table": file_table,
                "raw_data": raw_data}


ResourceFile = ResourceFileAdapter(RawResourceFile)


def unpack_res(file_path, dir_path):
    with open(file_path) as f:
        data = f.read()

    res = ResourceFile.parse(data)

    mkdir_p(dir_path)

    for file_name, file_data in res.items():
        with open(os.path.join(dir_path, file_name), "wb") as f:
            f.write(file_data)


def pack_res(dir_path, file_path):
    res_content = {}
    for root, dirs, files in os.walk(dir_path):
        for name in files:
            with open(os.path.join(root, name)) as f:
                res_content[name] = f.read()
        break

    with open(file_path, "wb") as f:
        f.write(ResourceFile.build(res_content))


if __name__ == "__main__":
    import sys

    test_folder(sys.argv[1], ".res", ResourceFile)
