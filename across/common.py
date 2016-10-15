from construct import *


class InlineArrayAdapter(Adapter):
    """
    Given a wrapped array structure where all fields except array are computed
    (eg. size + array + checksum), returns only array itself.

    This might be useful to remove unnecessary levels of indirection:
        level.polygons.data[0] -> level.polygons[0]
    """

    __slots__ = ["data_field"]

    def __init__(self, data_field, subcon):
        super(InlineArrayAdapter, self).__init__(subcon)
        self.data_field = data_field

    def _decode(self, obj, context):
        return obj[self.data_field]

    def _encode(self, obj, context):
        return Container({self.data_field: obj})


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


def ZeroString(length):
    return ZeroStringAdapter(Bytes(length))
