"""Raster -> SVG tracing without a browser.

Replaces the `svgtrace` package (which drives headless Chromium through playwright: ~90 MB of Node.js driver plus a
~300 MB Chromium download). It runs the same imagetracer.js (Unlicense / public domain, by Andras Jankovics) in an
embedded QuickJS engine, feeding it pixels loaded with Pillow through imagetracer's data entry point.
"""
import base64
import os
import re

from PIL import Image
import quickjs

_JS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'imagetracer.js')

_B64_JS = """
function __b64(s) {
    var T = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/', L = {}, i;
    for (i = 0; i < 64; i++) L[T.charAt(i)] = i;
    var n = s.length, pad = (s.charAt(n - 1) === '=') + (s.charAt(n - 2) === '='), out = new Uint8ClampedArray(n / 4 * 3 - pad), o = 0;
    for (i = 0; i < n; i += 4) {
        var v = (L[s.charAt(i)] << 18) | (L[s.charAt(i + 1)] << 12) | ((L[s.charAt(i + 2)] || 0) << 6) | (L[s.charAt(i + 3)] || 0);
        if (o < out.length) out[o++] = (v >> 16) & 255;
        if (o < out.length) out[o++] = (v >> 8) & 255;
        if (o < out.length) out[o++] = v & 255;
    }
    return out;
}
"""


def _options_js(mode):
    """A preset name becomes a JS string, an '{ key:value, ... }' option object is passed through."""
    mode = str(mode).strip()
    if mode.startswith('{'):
        mode = re.sub(r'\bTrue\b', 'true', mode)
        mode = re.sub(r'\bFalse\b', 'false', mode)
        return '(' + mode + ')'
    return '"%s"' % mode.replace('\\', '\\\\').replace('"', '\\"')


def trace(filename, blackAndWhite=False, mode="default"):
    """Same signature and result (an SVG string) as svgtrace.trace()."""
    if str(mode).find("black") >= 0 or blackAndWhite:
        mode = "posterized1"
    if not os.path.exists(filename):
        raise FileNotFoundError(f"{filename} does not exist!")

    img = Image.open(filename).convert('RGBA')
    width, height = img.size
    ctx = quickjs.Context()
    ctx.set_time_limit(600)
    ctx.set_memory_limit(2 * 1024 ** 3)
    ctx.eval("var self = this; var window = this;")
    with open(_JS_PATH, encoding='utf-8') as f:
        ctx.eval(f.read())
    ctx.eval(_B64_JS)
    ctx.set("__pixels", base64.b64encode(img.tobytes()).decode('ascii'))
    return ctx.eval(
        "ImageTracer.imagedataToSVG({width: %d, height: %d, data: __b64(__pixels)}, %s)"
        % (width, height, _options_js(mode)))
