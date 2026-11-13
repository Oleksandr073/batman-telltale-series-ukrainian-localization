"""Make the picture of the Telegram item in the main-menu feed: FEED_DIR/texture/ui_imageUATelegramFeed.d3dtx.

A QR code (the qr: line of feed_item.txt) on the left and line1..line3 on the right. Also writes
texture/preview.png and texture/preview_visible_band.png (red box = the part the game shows; not in git).
Needs Pillow and qrcode (`npm run setup:texture`) and the Windows fonts Segoe UI / Segoe UI Bold.

Usage (from the repo root):
  python make_feed_texture.py FEED_DIR [--if-available]
  e.g. data/feed_item
  --if-available (used by `npm run import`): if Pillow/qrcode or the fonts are missing, skip with a note and exit 0
  instead of stopping. Mistakes in feed_item.txt (bad qr link, text too wide) still stop with an error.

Game facts the layout is built on (checked in game 2026-11-13):
- feed pictures are 512x512, BC1/DXT1, 1 mip. D3DTX_HEADER below is the header of the game's
  ui_imageTelltaleAccountFeed.d3dtx with the name inside changed to ui_imageUATelegramFeed.d3dtx (and its two size
  fields); the file = that header + the BC1 pixels.
- the feed tile shows the full width but only rows ~113..316 of the texture; the rest is cut off
- classic mode tints feed pictures red, so the picture is black/white/gray (the QR still scans when tinted)
Exit code 1 on any error; nothing is written then.
"""
import os
import struct
import sys

from apply_feed_item import IMAGE, SETTINGS, check_url, fail, read_settings

D3DTX_HEADER = bytes.fromhex(
    '3656534dd1000000000000000000020007000000e2cc386f7e9e243e61ab30a7e388097a485d7f93b0cee3b28c590584'
    'b7fb888eaf7daca47aba6e8789886cfa0549485b071a1fe644a2bc7b02cc9fe10ff420e620baa1ef40fcf49aea0e30ae'
    'f119465861ea57500900000008000000110100000800000002000000240000001c00000075695f696d61676555415465'
    '6c656772616d466565642e643364747808000000000000000000803f3001000000000200000002000001000000010000'
    '0040000000000000000100000000000000000000000f0000000800000000010203000000410000c040000080bf000000'
    '000200000000000000000000000000803f0000803f080000000000000008000000000000000100000000000000000002'
    '00000000000000000001000000000002000004000000000200'
)
FONTS = os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts')
LINE_FONTS = [('segoeuib.ttf', 44), ('segoeui.ttf', 30), ('segoeui.ttf', 24)]  # line1, line2, line3
SIZE = 512
BAND_TOP, BAND_BOTTOM = 113, 316  # visible part of the texture


def make_image(qr_url, lines):
    from PIL import Image, ImageDraw, ImageFont
    import qrcode

    img = Image.new('RGB', (SIZE, SIZE), (24, 24, 24))
    d = ImageDraw.Draw(img)
    band_mid = (BAND_TOP + BAND_BOTTOM) // 2

    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=2, box_size=1)
    qr.add_data(qr_url)
    qr.make(fit=True)
    matrix = qr.get_matrix()  # includes the border
    n = len(matrix)
    box = 172 // n  # whole pixels per module
    if box < 4:
        fail(f'the qr: link is too long ({n} modules, {box} px each) - the code would be too small to scan')
    qr_size = n * box
    x0, y0 = 22, band_mid - qr_size // 2
    d.rectangle([x0, y0, x0 + qr_size - 1, y0 + qr_size - 1], fill=(255, 255, 255))
    for r, row in enumerate(matrix):
        for c, dark in enumerate(row):
            if dark:
                d.rectangle([x0 + c * box, y0 + r * box, x0 + (c + 1) * box - 1, y0 + (r + 1) * box - 1],
                            fill=(0, 0, 0))

    tx = x0 + qr_size + 22
    items = [(t, ImageFont.truetype(os.path.join(FONTS, f), s)) for t, (f, s) in zip(lines, LINE_FONTS) if t]
    heights = [font.getbbox(t)[3] - font.getbbox(t)[1] for t, font in items]
    gap = 14
    y = band_mid - (sum(heights) + gap * (len(items) - 1)) // 2
    for (text, font), h in zip(items, heights):
        width = font.getlength(text)
        if tx + width > SIZE - 10:
            fail(f'"{text}" is too wide ({int(width)} px, room for {SIZE - 10 - tx}) - make it shorter')
        d.text((tx, y - font.getbbox(text)[1]), text, font=font, fill=(235, 235, 235))
        y += h + gap
    return img, n, box


def bc1_block(px):
    """16 RGB pixels -> 8 bytes of BC1 (4-color mode)."""
    def to565(c):
        return ((c[0] >> 3) << 11) | ((c[1] >> 2) << 5) | (c[2] >> 3)

    def from565(v):
        r, g, b = (v >> 11) & 31, (v >> 5) & 63, v & 31
        return ((r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2))

    lum = [p[0] * 299 + p[1] * 587 + p[2] * 114 for p in px]
    hi, lo = px[lum.index(max(lum))], px[lum.index(min(lum))]
    c0, c1 = to565(hi), to565(lo)
    if c0 == c1:
        return struct.pack('<HHI', c0, c1, 0)
    if c0 < c1:
        c0, c1 = c1, c0
    e0, e1 = from565(c0), from565(c1)
    pal = [e0, e1, tuple((2 * a + b) // 3 for a, b in zip(e0, e1)), tuple((a + 2 * b) // 3 for a, b in zip(e0, e1))]
    bits = 0
    for i, p in enumerate(px):
        best = min(range(4), key=lambda k: sum((p[j] - pal[k][j]) ** 2 for j in range(3)))
        bits |= best << (2 * i)
    return struct.pack('<HHI', c0, c1, bits)


def bc1(img):
    pix = img.load()
    out = bytearray()
    for by in range(0, SIZE, 4):
        for bx in range(0, SIZE, 4):
            out += bc1_block([pix[bx + x, by + y] for y in range(4) for x in range(4)])
    return bytes(out)


def make_d3dtx(data):
    if IMAGE.encode() not in D3DTX_HEADER or len(D3DTX_HEADER) != 313 or len(data) != SIZE * SIZE // 2:
        fail('internal error: the d3dtx header or the pixel data has the wrong size')
    return D3DTX_HEADER + data


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    args = sys.argv[1:]
    if_available = '--if-available' in args
    if if_available:
        args.remove('--if-available')
    if len(args) != 1:
        print(__doc__)
        sys.exit(2)
    root = args[0]
    settings = os.path.join(root, SETTINGS)
    tex_dir = os.path.join(root, 'texture')
    if not os.path.isfile(settings):
        fail(f'missing file: {settings}')
    missing = []
    try:
        import PIL  # noqa: F401
        import qrcode  # noqa: F401
    except ImportError:
        missing.append('Pillow and qrcode are not installed - run `npm run setup:texture` once')
    for font, _ in LINE_FONTS:
        if not os.path.isfile(os.path.join(FONTS, font)):
            missing.append(f'font {font} not found in {FONTS}')
    if missing:
        if if_available:  # npm run import: skip the picture, don't stop the import
            print(f'Feed picture NOT remade ({"; ".join(missing)}). The picture in git is kept as it is.')
            sys.exit(0)
        fail('; '.join(missing))
    values = read_settings(settings)
    qr_url = values.get('qr', '')
    check_url(settings, qr_url, 'qr')
    lines = [values.get(k, '') for k in ('line1', 'line2', 'line3')]
    if not any(lines):
        fail(f'{settings}: give at least one of line1:, line2:, line3:')

    img, n, box = make_image(qr_url, lines)
    d3dtx = make_d3dtx(bc1(img))
    from PIL import ImageDraw
    img.save(os.path.join(tex_dir, 'preview.png'))
    band = img.copy()
    ImageDraw.Draw(band).rectangle([0, BAND_TOP, SIZE - 1, BAND_BOTTOM], outline=(255, 0, 0))
    band.save(os.path.join(tex_dir, 'preview_visible_band.png'))
    with open(os.path.join(tex_dir, IMAGE), 'wb') as fh:
        fh.write(d3dtx)
    print(f'QR: {n} modules x {box} px = {n * box} px -> {qr_url}')
    print(f'Written: {os.path.join(tex_dir, IMAGE)} (+ preview.png, preview_visible_band.png)')


if __name__ == '__main__':
    main()
