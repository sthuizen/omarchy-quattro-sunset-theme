#!/usr/bin/env python3
"""Check that the complete wallpaper collection matches its published catalog."""

import hashlib
import json
from pathlib import Path
import struct
import sys
import zlib


def png_dimensions(path):
    data = path.read_bytes()
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError(f'{path.name}: invalid PNG signature')
    offset = 8
    dimensions = None
    saw_end = False
    while offset < len(data):
        length = struct.unpack('>I', data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + length]
        crc = data[offset + 8 + length:offset + 12 + length]
        if len(payload) != length or len(crc) != 4:
            raise ValueError(f'{path.name}: truncated PNG chunk')
        if zlib.crc32(kind + payload) & 0xffffffff != struct.unpack('>I', crc)[0]:
            raise ValueError(f'{path.name}: invalid PNG chunk checksum')
        if kind == b'IHDR':
            dimensions = struct.unpack('>II', payload[:8])
        offset += 12 + length
        if kind == b'IEND':
            saw_end = True
            break
    if not dimensions or not all(dimensions) or not saw_end or offset != len(data):
        raise ValueError(f'{path.name}: invalid PNG structure')
    return data, dimensions


def main():
    root = Path(__file__).resolve().parents[1]
    catalog = json.loads((root / 'wallpapers.json').read_text())
    entries = catalog['wallpapers']
    paths = [entry['file'] for entry in entries]
    if len(entries) != 20 or len(set(paths)) != 20:
        raise ValueError('The catalog must contain exactly 20 distinct wallpapers')
    actual = {str(path.relative_to(root)) for path in (root / 'backgrounds').iterdir() if path.is_file()}
    if actual != set(paths):
        raise ValueError(f'Catalog differs from backgrounds/: {actual.symmetric_difference(paths)}')
    hashes = set()
    for entry in entries:
        path = root / entry['file']
        data, (width, height) = png_dimensions(path)
        digest = hashlib.sha256(data).hexdigest()
        if (width, height) != (entry['width'], entry['height']):
            raise ValueError(f'{path.name}: dimensions differ from the catalog')
        if digest != entry['sha256']:
            raise ValueError(f'{path.name}: SHA-256 differs from the catalog')
        if digest in hashes:
            raise ValueError(f'{path.name}: duplicate image content')
        hashes.add(digest)
    print('Verified 20 distinct PNG wallpapers: dimensions, PNG checksums, and SHA-256 hashes match.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, struct.error) as error:
        sys.exit(str(error))
