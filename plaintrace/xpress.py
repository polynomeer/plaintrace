"""Bounded XPRESS Huffman decoding per MS-XCA; no third-party runtime."""
from .binary import Binary, MAX_ARTIFACT_BYTES
from .evidence import AnalysisError


def decompress(data, expected_size):
    if type(expected_size) is not int or not 1 <= expected_size <= MAX_ARTIFACT_BYTES:
        raise AnalysisError("XPRESS advertised output size outside limits")
    raw = Binary(data, "XPRESS Huffman")
    output = bytearray()
    cursor = 0
    while len(output) < expected_size:
        packed = raw.take(cursor, 256)
        cursor += 256
        lengths = [value for byte in packed for value in (byte & 15, byte >> 4)]
        ordered = sorted((length, symbol) for symbol, length in enumerate(lengths) if length)
        codes, code, previous = {}, 0, 0
        for length, symbol in ordered:
            code <<= length - previous
            if code >= 1 << length:
                raise AnalysisError("Oversubscribed Huffman table")
            codes[(length, code)] = symbol
            code += 1
            previous = length
        if not ordered or code != 1 << previous:
            raise AnalysisError("Incomplete Huffman table")
        register = (raw.number(cursor,2) << 16) | raw.number(cursor+2,2)
        cursor += 4
        available = 32

        def bits(count):
            nonlocal register, available, cursor
            value = register >> (32-count) if count else 0
            register = (register << count) & 0xffffffff
            available -= count
            if available < 16:
                register |= raw.number(cursor,2) << (16-available)
                cursor += 2
                available += 16
            return value

        block_end = len(output) + 65536
        while len(output) < min(block_end, expected_size):
            prefix = 0
            for length in range(1,16):
                prefix = (prefix << 1) | bits(1)
                symbol = codes.get((length,prefix))
                if symbol is not None:
                    break
            else:
                raise AnalysisError("Invalid Huffman symbol")
            if symbol < 256:
                output.append(symbol)
                continue
            token = symbol - 256
            distance_bits, match_length = token >> 4, token & 15
            if match_length == 15:
                extended = raw.number(cursor,1)
                cursor += 1
                if extended == 255:
                    match_length = raw.number(cursor,2)
                    cursor += 2
                    if match_length < 15:
                        raise AnalysisError("Invalid XPRESS extended match")
                else:
                    match_length = extended + 15
            match_length += 3
            distance = (1 << distance_bits) + bits(distance_bits)
            if distance > len(output) or len(output) + match_length > expected_size:
                raise AnalysisError("XPRESS match outside output bounds")
            for _ in range(match_length):
                output.append(output[-distance])
    return bytes(output)
