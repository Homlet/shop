import sys
from PIL import Image
import zpl

def render(s):
    gutter = 4
    margin = 10
    lh = 4
    lines = s.splitlines()
    h = len(lines) * lh + margin
    l = zpl.Label(h, 80, 8)
    l.set_default_font(lh * 0.8, lh * 0.5, "F")
    i = 0
    for i in range(len(lines)):
        line = lines[i]
        if line == "":
            continue
        l.origin(gutter, i * lh + margin)
        l.write_text(line)
        l.endorigin()
    return l.dumpZPL()

if __name__ == "__main__":
    s = "".join(sys.stdin.readlines())
    print(render(s), end="")

