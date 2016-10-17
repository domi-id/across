from __future__ import print_function

import errno
import os

from construct import *


# noinspection PyPep8Naming
def InlineArrayAdapter(data_field, subcon):
    """
    Given a wrapped array structure where all fields except array are computed
    (eg. size + array + checksum), returns only array itself.

    This might be useful to remove unnecessary levels of indirection:
        level.polygons.data[0] -> level.polygons[0]
    """
    return ExprAdapter(subcon,
                       decoder=lambda obj, ctx: obj[data_field],
                       encoder=lambda obj, ctx: Container({data_field: obj}))


class SlicingAdapter(Adapter):
    """
    Adapter to convert a dict of several lists of the same length
    into a list of dicts and vice versa.

    {"a": [0, 1], "b": [2, 3]} -> [{"a": 0, "b": 2}, {"a": 1, "b": 3}]
    """

    def _decode(self, obj, context):
        # make sure obj only contains lists of the same length
        length = len(next(obj.values()))
        for v in obj.values():
            assert isinstance(v, ListContainer) and len(v) == length

        # second zip creates slices, first zip adds keys
        return ListContainer(Container(zip(obj.keys(), slice_))
                             for slice_ in zip(*obj.values()))

    def _encode(self, lst, context):
        # make sure all objects in list have same keys
        keys = set(lst[0].keys())
        assert all(set(obj.keys()) == keys for obj in lst)

        # for each key take a corresponding value from every object in the list
        return Container((key, ListContainer(x[key] for x in lst))
                         for key in lst[0].keys())


class ZeroStringAdapter(Adapter):
    """
    Special string type: string is zero-terminated,
    but doesn't exceed given length
    """

    def _decode(self, obj, context):
        if b"\x00" in obj:
            return obj[:obj.find(b"\x00")]
        return obj

    def _encode(self, obj, context):
        length = self.subcon.sizeof(context)
        obj = obj.ljust(length, b"\x00")
        if len(obj) > length:
            obj = obj[:length]
        return obj


# noinspection PyPep8Naming
def ZeroString(length):
    return ZeroStringAdapter(Bytes(length))


# noinspection PyPep8Naming
def PreallocatedArray(max_length, length, subcon):
    return Padded(max_length * subcon.sizeof(), Array(length, subcon))


# noinspection PyPep8Naming
def Boolean(subcon):
    return SymmetricMapping(subcon, {True: 1, False: 0})


def test_file(filepath, structure):
    with open(filepath, "rb") as f:
        data = f.read()

    # noinspection PyBroadException
    try:
        structure.build(structure.parse(data))
        print(filepath, "OK")
    except Exception as e:
        print(filepath, "FAILED", e)


def test_folder(path, extension, structure):
    for root, dirs, files in os.walk(path):
        for name in files:
            if name.lower().endswith(extension):
                test_file(os.path.join(root, name), structure)


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
