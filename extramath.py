import math

def sin(x):
    return math.sin(math.radians(x))

def cos(x):
    return math.cos(math.radians(x))

def atan2(y,x):
    return math.degrees(math.atan2(y,x)) % 360

def direction(obj1, obj2):
    return atan2(obj2.y - obj1.y, obj2.x - obj1.x)

def rotate_basis(dh1, dv1, gangle1, gangle2):
    dx = dh1 * cos(gangle1) - dv1 * sin(gangle1)
    dy = dh1 * sin(gangle1) + dv1 * cos(gangle1)

    dh2 = dx * cos(gangle2) + dy * sin(gangle2)
    dv2 = -dx * sin(gangle2) + dy * cos(gangle2)

    return (dh2, dv2)

def center_image(image):
    image.anchor_x = image.width/2
    image.anchor_y = image.height/2
