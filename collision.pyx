cdef inline int int_max(int a, int b): return a if a >= b else b
cdef inline int int_min(int a, int b): return a if a <= b else b

cdef inline int int_max_4(int a, int b, int c, int d):
    cdef int value = int_max(a, b)
    value = int_max(value, c)
    value = int_max(value, d)
    return value

cdef inline int int_min_4(int a, int b, int c, int d):
    cdef int value = int_min(a, b)
    value = int_min(value, c)
    value = int_min(value, d)
    return value

cdef inline void transform_rect(int width, int height, double co, 
        double si, double scaleX, double scaleY, int * r_x1, int * r_y1, int * r_x2, 
        int * r_y2):
    top_right_x = <int>(width * scaleX * co)
    top_right_y = <int>(-width * scaleX * si)
    bottom_left_x = <int>(height * scaleY * si)
    bottom_left_y = <int>(height * scaleY * co)
    bottom_right_x = <int>(width * scaleX * co + height * scaleY * si)
    bottom_right_y = <int>(height * scaleY * co - width * scaleX * si)
    r_x1[0] = int_min_4(0, top_right_x, bottom_left_x, bottom_right_x)
    r_x2[0] = int_max_4(0, top_right_x, bottom_left_x, bottom_right_x)
    r_y1[0] = int_min_4(0, top_right_y, bottom_left_y, bottom_right_y)
    r_y2[0] = int_max_4(0, top_right_y, bottom_left_y, bottom_right_y)

DEF PI = 3.141592653589793238462643

DEF PI_OVER_180 = 0.017453292519943295

cdef inline double radians(double degrees):
    return PI_OVER_180 * degrees
    
cdef extern from "math.h":
    double sin(double)
    double cos(double)
    double abs(double)
    double fabs(double)

from pyglet.image import ImageData

cdef extern from "pmask.c":
    ctypedef struct PMASK:
        pass
    void install_pmask()
    PMASK * create_pmask(int w, int h)
    void destroy_pmask(PMASK * mask)
    void pmask_load_pixels(PMASK *mask, void * pixels, int pitch, 
        int bytes_per_pixel, int trans_color)
    void set_pmask_pixel(PMASK * mask, int x, int y, int value)
    int get_pmask_pixel(PMASK * mask, int x, int y)
    int check_pmask_collision(PMASK * mask1, PMASK * mask2, int x1, int y1, 
        int x2, int y2)
    void fill_pmask(PMASK * mask, int value)
    void pmask_operation_or(PMASK *destination, PMASK * source, int x, int y)

cdef inline void intersect(int a_x1, int a_y1, int a_x2, int a_y2, 
                            int b_x1, int b_y1, int b_x2, int b_y2,
                            int * r_x1, int * r_y1, int * r_x2, int * r_y2):
    r_x1[0] = int_max(a_x1, b_x1)
    r_y1[0] = int_max(a_y1, b_y1)
    r_x2[0] = int_min(a_x2, b_x2)
    r_y2[0] = int_min(a_y2, b_y2)
    
def intersect_python(int a_x1, int a_y1, int a_x2, int a_y2, 
                            int b_x1, int b_y1, int b_x2, int b_y2):
    return (int_max(a_x1, b_x1), int_max(a_y1, b_y1), int_min(a_x2, b_x2),
        int_min(a_y2, b_y2))

cdef inline bint collides(int a_x1, int a_y1, int a_x2, int a_y2, 
                          int b_x1, int b_y1, int b_x2, int b_y2):
    if a_x2 <= b_x1 or a_y2 <= b_y1 or a_x1 >= b_x2 or a_y1 >= b_y2:
        return False
    return True

def collides_python(int a_x1, int a_y1, int a_x2, int a_y2, 
             int b_x1, int b_y1, int b_x2, int b_y2):
    return collides(a_x1, a_y1, a_x2, a_y2, b_x1, b_y1, b_x2, b_y2)

def collide_line(x1, y1, x2, y2, line_x1, line_y1, line_x2, line_y2):
    if line_x2 - line_x1 > line_y2 - line_y1:
        delta = float(line_y2 - line_y1) / (line_x2 - line_x1)
        if line_x2 > line_x1:
            if x2 < line_x1 or x1 >= line_x2:
                return False
        else:
            if x2 < line_x2 or x1 >= line_x1:
                return False
        y = delta * (x1 - line_x1) + line_y1
        if y >= y1 and y < y2:
            return True
        y = delta * (x2 - line_x1) + line_y1
        if y >= y1 and y < y2:
            return True
        return False
    else:
        delta = float(line_x2 - line_x1) / (line_y2 - line_y1)
        if line_y2 > line_y1:
            if y2 < line_y1 or y2 >= line_y2:
                return False
        else:
            if y2 < line_y2 or y1 >= line_y1:
                return False
        x = delta * (y1 - line_y1) + x1
        if x >= x1 and x < x2:
            return True
        x = delta * (y1 - line_y1) + x1
        if x >= x1 and x < x2:
            return True
        return False
            
import weakref
generated_masks = {}#weakref.WeakKeyDictionary()

cdef class MaskContainer:
    cdef PMASK * mask
    
    def __dealloc__(self):
        destroy_pmask(self.mask)

cdef class CollisionBase:
    cdef PMASK * mask
    cdef int width, height
    cdef bint isBounding
    cdef bint transform

    cdef void get_rect(self, int * r_x1, int * r_y1, int * r_x2, int * r_y2):
        pass # default does nothing
        
    cdef bint get_bit(self, int x, int y):
        return get_pmask_pixel(self.mask, x, y)

cdef class ObjectCollision(CollisionBase):
    cdef object sprite
    
    # transform stuff
    cdef double xScale, yScale
    cdef int angle
    cdef int x1, y1, x2, y2
    cdef double cosinus, sinus

    cdef void created(self):
        self.xScale = self.yScale = 1.0

    cpdef set_angle(self, int value):
        self.angle = value
        self.update_transform()
    
    cpdef set_scale(self, double xScale, double yScale):
        self.xScale = xScale
        self.yScale = yScale
        self.update_transform()
    
    cdef void update_transform(self):
        if self.xScale == 1.0 and self.yScale == 1.0 and self.angle == 0:
            self.transform = False
            return
        else:
            self.transform = True
        cdef double co, si
        co = cos(radians(self.angle))
        si = sin(radians(self.angle))
        cdef int x1, y1, x2, y2
        transform_rect(self.width, self.height, co, si, self.xScale, 
            self.yScale, &x1, &y1, &x2, &y2)
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.cosinus = cos(radians(-self.angle))
        self.sinus = sin(radians(-self.angle))
    
    cdef bint get_bit(self, int x, int y):
        if not self.transform:
            return get_pmask_pixel(self.mask, x, y)
        cdef int sourceX, sourceY
        x += self.x1
        y += self.y1
        sourceX = <int>(x / self.xScale * self.cosinus + 
            y / self.yScale * self.sinus)
        sourceY = <int>(y / self.yScale * self.cosinus - 
            x / self.xScale * self.sinus)
        if (sourceX >= 0 and sourceX < self.width 
        and sourceY >= 0 and sourceY < self.height):
            return get_pmask_pixel(self.mask, sourceX, sourceY)
        return False
    
    cdef void get_rect(self, int * r_x1, int * r_y1, int * r_x2, int * r_y2):
        r_x1[0] = self.sprite.left
        r_y1[0] = self.sprite.bottom
        r_x2[0] = self.sprite.right
        r_y2[0] = self.sprite.top

cdef class Collision(ObjectCollision):
    def __init__(self, sprite):
        self.sprite = sprite
        image = sprite.texture.get_image_data()
        self.width = image.width
        self.height = image.height
        cdef MaskContainer maskContainer
        cdef PMASK * bitmask
        cdef char * mask
        
        cdef int x, y, value
        if image in generated_masks:
            bitmask = (<MaskContainer>generated_masks[image]).mask
        else:
            bitmask = create_pmask(self.width, self.height)
            alphaMask = image.get_data('A', self.width)
            mask = alphaMask

            for x in range(self.width):
                for y in range(self.height):
                    if mask[x + y * self.width]:
                        value = 1
                    else:
                        value = 0
                    set_pmask_pixel(bitmask, x, y, value)

            maskContainer = MaskContainer()
            maskContainer.mask = bitmask
            generated_masks[image] = maskContainer

        self.mask = bitmask
        self.created()

cdef inline PMASK * make_rectangle_mask(int width, int height):
    cdef PMASK * mask = create_pmask(width, height)
    cdef int x, y
    for x in range(width):
        for y in range(height):
            set_pmask_pixel(mask, x, y, 1)
    return mask

cdef class BoundingBox(ObjectCollision):
    def __init__(self, sprite):
        image = sprite.texture
        self.width = image.width
        self.height = image.height
        self.sprite = sprite
        self.mask = make_rectangle_mask(self.width, self.height)
        self.created()
        self.isBounding = True
    
    def __dealloc__(self):
        destroy_pmask(self.mask)
    
    def resize(self, width, height):
        destroy_pmask(self.mask)
        self.mask = make_rectangle_mask(self.width, self.height)

cdef class Rectangle(CollisionBase):
    def __init__(self, int x, int y, int width, int height):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height
        self.width = width
        self.height = height
        self.mask = make_rectangle_mask(self.width, self.height)
        self.isBounding = True
        
    def __dealloc__(self):
        destroy_pmask(self.mask)
    
    cdef void get_rect(self, int * r_x1, int * r_y1, int * r_x2, int * r_y2):
        r_x1[0] = self.x1
        r_y1[0] = self.y1
        r_x2[0] = self.x2 + 1
        r_y2[0] = self.y2 + 1

cdef PMASK * point_mask = make_rectangle_mask(1, 1)

cdef class Point(CollisionBase):
    def __init__(self, int x, int y):
        self.x1 = x
        self.y1 = y
        self.x2 = x + 1
        self.y2 = y + 1
        self.width = 1
        self.height = 1
        self.mask = point_mask
        self.isBounding = True
    
    def set_position(self, x, y):
        self.x1 = x
        self.y1 = y
        self.x2 = x + 1
        self.y2 = y + 1
        
    cdef void get_rect(self, int * r_x1, int * r_y1, int * r_x2, int * r_y2):
        r_x1[0] = self.x1
        r_y1[0] = self.y1
        r_x2[0] = self.x2 + 1
        r_y2[0] = self.y2 + 1

install_pmask()

cdef inline bint collide(CollisionBase lhs, CollisionBase rhs):
    cdef int a_x1, a_y1, a_x2, a_y2, b_x1, b_y1, b_x2, b_y2
    lhs.get_rect(&a_x1, &a_y1, &a_x2, &a_y2)
    rhs.get_rect(&b_x1, &b_y1, &b_x2, &b_y2)
    if not (lhs.transform or rhs.transform):
        return check_pmask_collision(lhs.mask, rhs.mask, a_x1, a_y1, b_x1, 
            b_y1)
    # we're transformed <3
    if not collides(a_x1, a_y1, a_x2, a_y2, b_x1, b_y1, b_x2, b_y2):
        return False
    if lhs.isBounding and rhs.isBounding:
        return True
    cdef int x1, y1, x2, y2
    # calculate the overlapping area
    intersect(a_x1, a_y1, a_x2, a_y2, b_x1, b_y1, b_x2, b_y2,
        &x1, &y1, &x2, &y2)
    # figure out the offsets of the overlapping area in each sprite
    cdef int offx1 = x1 - a_x1
    cdef int offy1 = y1 - a_y1
    cdef int offx2 = x1 - b_x1
    cdef int offy2 = y1 - b_y1
    
    cdef bint bounding1 = lhs.isBounding
    cdef bint bounding2 = rhs.isBounding
    
    cdef int c1, c2, x, y
    # for each overlapping pixel, check for a collision
    for x in range(x2 - x1):
        for y in range(y2 - y1):
            if bounding1:
                c1 = 1
            else:
                c1 = lhs.get_bit(offx1+x, y + offy1)
            if bounding2:
                c2 = 1
            else:
                c2 = rhs.get_bit(offx2+x, y + offy2)
            if c1 and c2:
                return 1
    return 0

def collide_python(lhs, rhs):
    return collide(lhs, rhs)