from __future__ import division

from io import StringIO

import svgwrite

from .point import Point

__all__ = ['get_drawing_string']


def get_y(x, p1, p2):
    return p1.y + (x - p1.x) * (p2.y - p1.y) / (p2.x - p1.x)


def nearest_humanlike(x):
    return min((0.01, 0.1, 0.2, 0.3, 0.5, 1, 5, 10, 20, 30, 40, 50, 100,
                200, 300, 400, 500, 1000, 2000, 3000, 4000, 5000, 10000),
               key=lambda t: abs(t - x))


def segment(self, p1, p2, stroke, stroke_width=4, stroke_dasharray=None, **kwargs):
    extra = {'stroke-width': str(stroke_width), 'stroke-linecap': 'round'}
    extra.update(kwargs)
    if stroke_dasharray:
        extra['stroke-dasharray'] = stroke_dasharray
    self.add(self.line((float(p1.x), float(p1.y)), (float(p2.x), float(p2.y)), stroke=stroke, **extra))


def label(self, s, pos, fill='black', text_anchor='start', **kwargs):
    extra = {'text-anchor': text_anchor}
    extra.update(kwargs)
    self.add(self.text(s, insert=(pos.x, pos.y), fill=fill, **extra))


def get_drawing_string(model, T12, T34, g1, g3, names, width, height, threshold_g, color_background, color_tree, color_hybrid, color_ruler):
    assert model in ('H1', 'H2'), "Model must me either H1 or H2"
    assert T12 >= 0, "T12 must be positive"
    assert T34 >= 0, "T34 must be positive"
    assert 0 <= g1 and g1 <= 1, "g1 must be in [0..1]"
    assert 0 <= g3 and g3 <= 1, "g3 must be in [0..1]"
    assert len(names) == 4, "There must be exactly 4 names"

    if color_background == 'transparent':
        color_background = None

    marginTop = 15
    marginBot = 0
    marginLeft = 0
    marginRight = 0
    rootWidth = 40

    xPreRoot = marginLeft
    xRoot = xPreRoot + rootWidth
    xEnd = width - marginRight
    Tpx = 0.6 * (xEnd - xRoot)
    if T12 == 0 and T34 == 0:
        xCD = xRoot
    else:
        xCD = xRoot + Tpx
    try:
        xAB = xRoot + (xCD - xRoot) * T12 / (T12 + T34)
    except ZeroDivisionError:
        xAB = xCD

    y1 = marginTop
    gap = (height - marginTop - marginBot) / 3.
    y2 = y1 + 3 * gap
    if model == 'H1':
        y3 = y1 + gap
        y4 = y1 + 2 * gap
    elif model == 'H2':
        y3 = y1 + 2 * gap
        y4 = y1 + gap
    yRoot = y1 + 1.5 * gap

    rulerPx = 0.2 * (xEnd - xRoot)
    mya_per_px = (T12 + T34) / Tpx
    if mya_per_px > 1e-6:
        rulerMya = nearest_humanlike(mya_per_px * rulerPx)
        rulerSize = rulerMya / mya_per_px
    else:
        rulerMya = 0
        rulerSize = 0
    xRulerStart = xRoot
    xRulerEnd = xRulerStart + rulerSize
    xRulerLabel = xRulerStart + rulerSize / 2.
    yRuler = y1 + 2.7 * gap

    pPreRoot = Point(xPreRoot, yRoot)
    pRoot = Point(xRoot, yRoot)
    pRulerStart = Point(xRulerStart, yRuler)
    pRulerEnd = Point(xRulerEnd, yRuler)
    pRulerLabel = Point(xRulerLabel, yRuler - 5)
    p1 = Point(xEnd, y1)
    p2 = Point(xEnd, y2)
    p3 = Point(xEnd, y3)
    p4 = Point(xEnd, y4)

    if model == 'H1':
        yA = get_y(xAB, pRoot, p1)
        yB = get_y(xAB, pRoot, p2)
        yD = get_y(xCD, pRoot, p2)

        lAB = yB - yA
        yAB = yA + (1 - g1) * lAB
        pAB = Point(xAB, yAB)

        yC = get_y(xCD, pAB, p3)

        lCD = yD - yC
        if T34 == 0 and g1 == 0:
            assert abs(xAB - xCD) < 1e-3, 'if T34=0 and g1=0, then xAB must be equal to xCD'
            # g3 is meaningless when T34=0 and g1=0
            yCD = yAB
        else:
            yCD = yC + (1 - g3) * lCD
        pCD = Point(xCD, yCD)
    elif model == 'H2':
        yA = get_y(xAB, pRoot, p1)
        yB = get_y(xAB, pRoot, p2)
        yC = get_y(xCD, pRoot, p1)
        yD = get_y(xCD, pRoot, p2)

        lAB = yB - yA
        yAB = yA + (1 - g1) * lAB
        pAB = Point(xAB, yAB)

        lCD = yD - yC
        if T34 == 0 and g1 == 0:
            assert abs(xAB - xCD) < 1e-3, 'if T34=0 and g1=0, then xAB must be equal to xCD'
            # g3 is meaningless when T34=0 and g1=0
            yCD = yAB
        else:
            yCD = yC + (1 - g3) * lCD
        pCD = Point(xCD, yCD)

        # if pAB is above pCD then flip 3 and 4
        if yAB < yCD:
            p3, p4 = p4, p3

    pA = Point(xAB, yA)
    pB = Point(xAB, yB)
    pC = Point(xCD, yC)
    pD = Point(xCD, yD)

    dwg = svgwrite.Drawing(profile='tiny')
    # Monkey-patch:
    dwg.segment = segment
    dwg.label = label

    if color_background is not None:
        dwg.add(dwg.rect((0, 0), size=('100%', '100%'), rx=None, ry=None, fill=color_background))
        # dwg.add(dwg.rect((0, 0), size=(width, height), rx=None, ry=None, fill=color_background))

    if threshold_g <= g1 and g1 <= (1 - threshold_g) and T12 > 0:
        dwg.segment(pA, pB, stroke=color_hybrid, stroke_width=3, stroke_dasharray='12')
    if threshold_g <= g3 and g3 <= (1 - threshold_g) and T34 > 0:
        dwg.segment(pC, pD, stroke=color_hybrid, stroke_width=3, stroke_dasharray='12')
    dwg.segment(pPreRoot, pRoot, stroke=color_tree)
    dwg.segment(pRoot, p1, stroke=color_tree)
    dwg.segment(pRoot, p2, stroke=color_tree)
    dwg.segment(pAB, p3, stroke=color_tree)
    dwg.segment(pCD, p4, stroke=color_tree)
    dwg.label(names[0], p1 + Point(2, 0))
    dwg.label(names[1], p2 + Point(2, 0))
    dwg.label(names[2], p3 + Point(2, 0))
    dwg.label(names[3], p4 + Point(2, 0))
    dwg.segment(pRulerStart, pRulerEnd, stroke=color_ruler)
    dwg.label(str(rulerMya), pRulerLabel, text_anchor='middle')

    s = StringIO()
    dwg.write(s, pretty=True)
    return s.getvalue()
