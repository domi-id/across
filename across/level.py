#!/usr/bin/env python

import random

from construct import *

from common import ZeroString, InlineArrayAdapter, test_folder


OBJECT_TYPES = dict(flower=1, apple=2, killer=3, start=4)
CLIPPING = dict(none=0, ground=1, sky=2)
GRAVITY = dict(none=0, up=1, down=2, left=3, right=4)


def level_hash(level):
    result = 0.0

    for polygon in level.polygons:
        for vertex in polygon.vertices:
            result += vertex.x + vertex.y

    for obj in level.objects:
        result += obj.x + obj.y + OBJECT_TYPES[obj.type]

    if "pictures" in level:
        for picture in level.pictures:
            result += picture.x + picture.y

    return result * 3247.764325643


def integrity_computer(base, range):
    def integrity(level):
        return random.randint(base, base + range - 1) - level.integrity_1

    return integrity


def level_integrity(level):
    tests = (
        abs(level_hash(level) - level.integrity_1) < 0.000001,
        9786 <= level.integrity_1 + level.integrity_2 < 36546,
        9786 <= level.integrity_1 + level.integrity_3 < 36546,
        9875 <= level.integrity_1 + level.integrity_4 < 32345
    )

    return all(tests)


# noinspection PyPep8Naming,PyPep8,PyUnresolvedReferences
def FloatPrefixedArray(magic_number, subcon):
    return InlineArrayAdapter("data", Struct(
        "count" / Rebuild(Float64l, lambda ctx: len(ctx.data) + magic_number),
        "data"  / Array(lambda ctx: int(ctx.count), subcon)
    ))


# noinspection PyUnresolvedReferences
Point2D = Struct(
    "x" / Float64l,
    "y" / Float64l
)

# noinspection PyPep8,PyUnresolvedReferences
BasePolygon = Struct(
    "vertex_num" / Rebuild(Int32ul, len_(this.vertices)),
    "vertices"   / Array(this.vertex_num, Point2D)
)

# noinspection PyPep8,PyUnresolvedReferences
BaseObject = Struct(
    Embedded(Point2D),
    "type" / Enum(Int32ul, **OBJECT_TYPES),
)

# noinspection PyPep8,PyUnresolvedReferences
BasePicture = Struct(
    "pic_name" / ZeroString(10),
    "tex_name" / ZeroString(10),
    "msk_name" / ZeroString(10),
    Embedded(Point2D),
    "distance" / Int32ul,
    "clipping" / Enum(Int32ul, **CLIPPING)
)

# noinspection PyUnresolvedReferences
ElmaPolygon = Struct(
    "grass" / Int32ul,
    Embedded(BasePolygon)
)

# noinspection PyPep8,PyUnresolvedReferences
ElmaObject = Struct(
    Embedded(BaseObject),
    "gravity"   / Enum(Int32ul, **GRAVITY),
    "animation" / Int32ul
)

# noinspection PyPep8,PyUnresolvedReferences
Header06 = Padded(100, Struct(
    "version"     / Const(b"POT06"),
    "link_number" / Int32ul,
    "integrity_1" / Rebuild(Float64l, level_hash),
    "integrity_2" / Rebuild(Float64l, integrity_computer(11877, 5871)),
    "integrity_3" / Rebuild(Float64l, integrity_computer(11877, 5871)),
    "integrity_4" / Rebuild(Float64l, integrity_computer(12112, 6102)),
    "title"       / ZeroString(15)
))

# noinspection PyPep8,PyUnresolvedReferences
Header14 = Struct(
    "version"     / Const(b"POT14"),
    Padding(2),
    "link_number" / Int32ul,
    "integrity_1" / Float64l,
    "integrity_2" / Float64l,
    "integrity_3" / Float64l,
    "integrity_4" / Float64l,
    "title"       / ZeroString(51),
    "lgr"         / ZeroString(16),
    "ground"      / ZeroString(10),
    "sky"         / ZeroString(10)
)

# noinspection PyPep8,PyUnresolvedReferences
Level06 = Struct(
    Embedded(Header06),
    "polygons" / FloatPrefixedArray(0.4643643, BasePolygon),
    "objects"  / FloatPrefixedArray(0.4643643, BaseObject)
)

# noinspection PyPep8,PyUnresolvedReferences
Level14 = Struct(
    Embedded(Header14),
    "polygons" / FloatPrefixedArray(0.4643643, ElmaPolygon),
    "objects"  / FloatPrefixedArray(0.4643643, ElmaObject),
    "pictures" / FloatPrefixedArray(0.2345672, BasePicture)
)

# noinspection PyUnresolvedReferences
Level = Struct(
    Embedded(Select(Level14, Level06)),
    Check(level_integrity)
)


if __name__ == "__main__":
    import sys

    test_folder(sys.argv[1], ".lev", Level)
