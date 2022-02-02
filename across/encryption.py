from construct import RestreamedBytesIO, Subconstruct


class CryptoStream(object):
    def __init__(self, stream, length, params):
        self.a, self.b, self.c, self.d = params
        self.stream = RestreamedBytesIO(stream,
                                        self.crypt, length,
                                        self.crypt, length)

    def __enter__(self):
        return self.stream

    def __exit__(self, typ, value, tb):
        self.stream.close()

    @staticmethod
    def signed_mod(a, b):
        a = a & 0xFFFF
        r = a % b
        if a > 0x7FFF:
            return -b + (r - 0x10000) % b
        return r

    def crypt(self, data):
        result = [data[0] ^ self.a]

        x = (self.b + self.a * self.c) * self.d + self.c
        for s in data[1:]:
            result.append(s ^ (x & 0xFF))
            x += self.signed_mod(x, self.c) * (self.c * self.d)

        return bytes(result)


class EncryptedBlock(Subconstruct):
    __slots__ = ["params"]

    def __init__(self, params, subcon):
        super(EncryptedBlock, self).__init__(subcon)
        self.params = params

    # noinspection PyProtectedMember
    def _parse(self, stream, context, path):
        length = self.subcon.sizeof(context)
        with CryptoStream(stream, length, self.params) as crypto_stream:
            return self.subcon._parse(crypto_stream, context, path)

    # noinspection PyProtectedMember
    def _build(self, obj, stream, context, path):
        length = self.subcon.sizeof(context)
        with CryptoStream(stream, length, self.params) as crypto_stream:
            return self.subcon._build(obj, crypto_stream, context, path)
