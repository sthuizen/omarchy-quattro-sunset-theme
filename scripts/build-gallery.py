#!/usr/bin/env python3
"""Compose a labeled gallery from the original wallpapers using ImageMagick."""

import json
from pathlib import Path
import subprocess
import tempfile


def main():
    root = Path(__file__).resolve().parents[1]
    subprocess.run(['python3', str(root / 'scripts/check-wallpapers.py')], check=True)
    entries = json.loads((root / 'wallpapers.json').read_text())['wallpapers']
    output = root / 'previews/wallpaper-gallery.webp'
    output.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='quattro-sunset-gallery-') as temporary:
        tiles = []
        for number, entry in enumerate(entries, 1):
            tile = Path(temporary) / f'{number:02}.png'
            subprocess.run([
                'magick', str(root / entry['file']), '-auto-orient',
                '-thumbnail', '480x270', '-background', '#130D0B',
                '-gravity', 'center', '-extent', '480x270',
                '-gravity', 'south', '-background', '#2A1A10', '-splice', '0x46',
                '-font', 'Liberation-Sans', '-pointsize', '17', '-fill', '#E7C7A0',
                '-annotate', '+0+14', f'{number:02}  {entry["title"]}', str(tile),
            ], check=True)
            tiles.append(str(tile))
        subprocess.run([
            'magick', 'montage', *tiles, '-tile', '4x5', '-geometry', '+10+10',
            '-background', '#130D0B', '-quality', '86', str(output),
        ], check=True)
    print(f'Wrote {output.relative_to(root)}')


if __name__ == '__main__':
    main()
