#!/usr/bin/env python
from construct import *


class Across10Internal(Adapter):
    LEVEL_MAPPING = {
        11: 81, 12: 11, 13: 82, 14: 84, 15: 17, 16: 83, 17: 18,
        18: 19, 19: 20, 20: 21, 21: 22, 22: 80, 23: 38
    }

    def __init__(self, subcon):
        super(Across10Internal, self).__init__(subcon)

    def _decode(self, obj, context):
        assert obj <= 23
        if obj in self.LEVEL_MAPPING:
            return self.LEVEL_MAPPING[obj]
        return obj

    def _encode(self, obj, context):
        for k, v in self.LEVEL_MAPPING.iteritems():
            if obj == v:
                return k
        assert obj <= 23
        return obj


# noinspection PyPep8,PyUnresolvedReferences
Event = Struct(
    "time" / Float64l,
    "data" / Bytes(8)
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
        "data_1" / Array(this._.frames_num, Float32l),
        "data_2" / Array(this._.frames_num, Float32l),
        "data_3" / Array(this._.frames_num, Float32l),
        "data_4" / Array(this._.frames_num, Float32l),
        "data_5" / Array(this._.frames_num, Float32l),
        "data_6" / Array(this._.frames_num, Float32l),
        "data_7" / Array(this._.frames_num, Float32l),
        "data_8" / Array(this._.frames_num, Float32l),
        "data_9" / Array(this._.frames_num, Float32l),
        "data_A" / Array(this._.frames_num, Int8ul),
        "data_B" / Array(this._.frames_num, Float32l),
        "data_C" / Array(this._.frames_num, Int8ul),
        "data_D" / Array(this._.frames_num, Float32l),
        "data_E" / Array(this._.frames_num, Float32l)
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
