def collide_line_line((x1, y1, x2, y2), (x3, y3, x4, y4))
    denom = (y4 - y3)*(x2 - x1) - (x4 - x3)*(y2 - y1)
    if denom == 0:
        return False#None
    ua = ((x4 - x3)*(y1 - y3) - (y4 - y3)*(x1 - x3)) / denom
    ub = ((x2 - x1)*(y1 - y3) - (y2 - y1)*(x1 - x3)) / denom
    if ua >= 0 and ua <= 1 and ub >= 0 and ub <= 1:
        # ix = x1 + ua*(x2 - x1)
        # iy = y1 + ua*(y2 - y1)
        # distance2 = (ix - x1)**2 + (iy - y1)**2
        return True#distance2, (x4-x3, y4-y3), (ix, iy)
    return False#None

def collide_rectangle_triangle((x1, y1, x2, y2), (x3, y3, x4, y4, x5, y5)):
    triangle_lines = [(x3, y3, x4, y4), (x3, y3, x5, y5), (x4, y4, x5, y5)]
    rectangle_lines = [(x1, y1, x2, y1), (x1, y1, x1, y2), (x1, y2, x2, y2),
        (x2, y2, x2, y1)]
    for triangle_line in triangle_lines:
        for rectangle_line in rectangle_lines:
            if collide_line_line(triangle_line, rectangle_line):
                return True
    return False

