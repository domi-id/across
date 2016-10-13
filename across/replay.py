#!/usr/bin/env python
from construct import *


class Across10Internal(Adapter):
    LEVEL_MAPPING = {
        11: 81, 12: 11, 13: 82, 14: 84, 15: 17, 16: 83, 17: 18,
        18: 19, 19: 20, 20: 21, 21: 22, 22: 80, 23: 38
    }

    ACROSS10_LEVELS = 24

    def __init__(self, subcon):
        super(Across10Internal, self).__init__(subcon)

    def _decode(self, obj, context):
        assert obj < self.ACROSS10_LEVELS
        if obj in self.LEVEL_MAPPING:
            return self.LEVEL_MAPPING[obj]
        return obj

    def _encode(self, obj, context):
        for k, v in self.LEVEL_MAPPING.iteritems():
            if obj == v:
                return k
        assert obj < self.ACROSS10_LEVELS
        return obj


# noinspection PyPep8,PyUnresolvedReferences
Event = Struct(
    "time"   / Float64l,
    "object" / Int16sl,
    "type"   / Int8ul,
               Int8ul,
    "volume" / Float32l,
    IfThenElse(this.type == 0,
               Check(this.object >= 0),
               Check(this.object == -1))
)

# noinspection PyPep8,PyUnresolvedReferences
Across10Header = Struct(
    "version"      / Computed(lambda ctx: 100),
    "link_number"  / Computed(lambda ctx: 0),
    "internal_num" / Across10Internal(Int32ul)
)

# noinspection PyPep8,PyUnresolvedReferences
Across12Header = Struct(
    "version"      / Const(Int32ul, 120),
    "link_number"  / Int32ul,
    "internal_num" / Int32ul,
    IfThenElse(this.link_number > 0,
               Check(this.internal_num == 0xFFFFFFFF),
               Check(this.internal_num <= 90))
)

# noinspection PyProtectedMember,PyPep8,PyUnresolvedReferences
Replay = Struct(
    "frames_num" / Int32ul,
    Embedded(Select(Across12Header, Across10Header)),
    Embedded(Struct(
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
    "events_num" / Int32ul,
    "events"     / Array(this.events_num, Event),
    "end_marker" / Const(Int32ul, 4796277)
)


def test_replay(filepath):
    with open(filepath) as f:
        # noinspection PyBroadException
        try:
            Replay.parse(f.read())
            print filepath, "OK"
        except Exception as e:
            print filepath, "FAILED", e


if __name__ == "__main__":
    import os
    import sys

    for root, dirs, files in os.walk(sys.argv[1]):
        for name in files:
            if name.lower().endswith(".rec"):
                test_replay(os.path.join(root, name))
