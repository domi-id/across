#!/usr/bin/env python
from __future__ import print_function

from construct import *


class Across10InternalAdapter(Adapter):
    """
    Adapter to convert internal level number between Across 1.0 and Across 1.2
    numbering systems.

    In Across 1.0 and 1.1 levels are numbered [0..23] inclusive.
    In Across 1.2+ levels are numbered [0..99] and some of the original levels
    have a different number there, hence the mapping dict.
    """

    LEVEL_MAPPING = {
        11: 81, 12: 11, 13: 82, 14: 84, 15: 17, 16: 83, 17: 18,
        18: 19, 19: 20, 20: 21, 21: 22, 22: 80, 23: 38
    }

    ACROSS10_LEVELS = 24

    def _decode(self, obj, context):
        assert obj < self.ACROSS10_LEVELS
        if obj in self.LEVEL_MAPPING:
            return self.LEVEL_MAPPING[obj]
        return obj

    def _encode(self, obj, context):
        for k, v in self.LEVEL_MAPPING.items():
            if obj == v:
                return k
        assert obj < self.ACROSS10_LEVELS
        return obj


class SlicingAdapter(Adapter):
    """
    Adapter to convert a dict of several lists of the same length
    into a list of dicts and vice versa.

    {"a": [0, 1], "b": [2, 3]} -> [{"a": 0, "b": 2}, {"a": 1, "b": 3}]
    """

    def _decode(self, obj, context):
        # make sure obj only contains lists of the same length
        length = len(obj.values().next())
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


def event_integrity(event):
    if event.type == "object_taken":
        return event.object >= 0
    return event.object == -1


def header_integrity(header):
    if header.link_number > 0:
        return header.internal_num == -1
    return 0 <= header.internal_num < 100


# noinspection PyPep8,PyUnresolvedReferences
Event = Struct(
    "time"   / Float64l,
    "object" / Int16sl,
    "type"   / Padded(2, Enum(Int8ul, object_taken=0, bounce=1, failure=2,
                                      success=3, apple=4, changedir=5,
                                      right_volt=6, left_volt=7)),
    "volume" / Float32l,
    Check(event_integrity)
)

# noinspection PyPep8,PyUnresolvedReferences
Across10Header = Struct(
    "version"      / Computed(100),
    "link_number"  / Computed(0),
    "internal_num" / Across10InternalAdapter(Int32ul)
)

# noinspection PyPep8,PyUnresolvedReferences
Across12Header = Struct(
    "version"      / Const(Int32ul, 120),
    "link_number"  / Int32ul,
    "internal_num" / Int32sl,
    Check(header_integrity)
)

# noinspection PyProtectedMember,PyPep8,PyUnresolvedReferences
Replay = Struct(
    "frames_num" / Rebuild(Int32ul, len_(this.frames)),
    Embedded(Select(Across12Header, Across10Header)),
    "frames"     / SlicingAdapter(Struct(
        "bike_x"     / Array(this._.frames_num, Float32l),
        "bike_y"     / Array(this._.frames_num, Float32l),
        "lwhl_x"     / Array(this._.frames_num, Float32l),
        "lwhl_y"     / Array(this._.frames_num, Float32l),
        "rwhl_x"     / Array(this._.frames_num, Float32l),
        "rwhl_y"     / Array(this._.frames_num, Float32l),
        "bike_a"     / Array(this._.frames_num, Float32l),
        "lwhl_a"     / Array(this._.frames_num, Float32l),
        "rwhl_a"     / Array(this._.frames_num, Float32l),
        "direction"  / Array(this._.frames_num, Enum(Int8ul, left=0, right=1)),
        "engine_rpm" / Array(this._.frames_num, Float32l),
        "throttling" / Array(this._.frames_num, Flag),
        "friction_1" / Array(this._.frames_num, Float32l),
        "friction_2" / Array(this._.frames_num, Float32l)
    )),
    "events_num" / Rebuild(Int32ul, len_(this.events)),
    "events"     / Array(this.events_num, Event),
    "end_marker" / Const(Int32ul, 0x492f75)
)


def test_replay(filepath):
    with open(filepath, "rb") as f:
        data = f.read()

    # noinspection PyBroadException
    try:
        Replay.build(Replay.parse(data))
        print(filepath, "OK")
    except Exception as e:
        print(filepath, "FAILED", e)


def test_folder(path):
    for root, dirs, files in os.walk(path):
        for name in files:
            if name.lower().endswith(".rec"):
                test_replay(os.path.join(root, name))


if __name__ == "__main__":
    import os
    import sys

    test_folder(sys.argv[1])
