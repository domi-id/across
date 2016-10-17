#!/usr/bin/env python

from construct import *

from common import SlicingAdapter, Boolean, test_folder

EVENT_TYPES = dict(object_taken=0, bounce=1, failure=2, success=3, apple=4,
                   changedir=5, right_volt=6, left_volt=7)

BIKE_DIR = dict(left=0, right=1)


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
    "type"   / Padded(2, Enum(Int8ul, **EVENT_TYPES)),
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
        "direction"  / Array(this._.frames_num, Enum(Int8ul, **BIKE_DIR)),
        "engine_rpm" / Array(this._.frames_num, Float32l),
        "throttling" / Array(this._.frames_num, Boolean(Int8ul)),
        "friction_1" / Array(this._.frames_num, Float32l),
        "friction_2" / Array(this._.frames_num, Float32l)
    )),
    "events" / PrefixedArray(Int32ul, Event),
    Const(Int32ul, 0x492f75)
)


if __name__ == "__main__":
    import sys

    test_folder(sys.argv[1], ".rec", Replay)
