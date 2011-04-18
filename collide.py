# needed to cast image data
from ctypes import *

class Rect:
        '''Fast rectangular collision structure'''
        
        def __init__(self, x1, y1, x2, y2):
                '''Create a rectangle from a minimum and maximum point'''
                self.x1, self.y1 = x1, y1
                self.x2, self.y2 = x2, y2
                
        def intersect(self, r):
                '''Compute the intersection of two rectangles'''
                n = Rect( max(self.x1, r.x1), max(self.y1, r.y1), min(self.x2, r.x2), min(self.y2, r.y2) )
                return n
                
        def collides(self, r):
                '''Determine whether two rectangles collide'''
                if self.x2 < r.x1 or self.y2 < r.y1 or self.x1 > r.x2 or self.y1 > r.y2:
                        return False
                return True
        
        @property
        def width(self):
                return self.x2 - self.x1
        
        @property
        def height(self):
                return self.y2 - self.y1
        
        def __repr__(self):
                return '[%d %d %d %d]' % (self.x1, self.y1, self.x2, self.y2)
        
        @staticmethod
        def from_sprite(s):
                '''Create a rectangle matching the bounds of the given sprite'''
                i = (s._texture if not s._animation else s._animation.frames[s._frame_index].image)
                x = int(s.x - i.anchor_x)
                y = int(s.y - i.anchor_y)
                return Rect(x, y, x + s.width, y + s.height)

# pyglet.image.get_image_data() is very slow
# so we cache generated data
image_data_cache = {}

class SpriteCollision:
        '''Collision structure for a sprite'''
        
        def __init__(self, sprite):
                self.s = sprite
        
        def get_image(self):
                '''Returns the (potentially cached) image data for the sprite'''
                
                # if this is an animated sprite, grab the current frame
                if self.s._animation:
                        i = self.s._animation.frames[self.s._frame_index].image
                # otherwise just grab the image
                else:
                        i = self.s._texture
                
                # if the image is already cached, use the cached copy
                if i in image_data_cache:
                        d = image_data_cache[i]
                # otherwise grab the image's alpha channel, and cache it
                else:
                        d = i.get_image_data().get_data('A', i.width)
                        image_data_cache[i] = d
                
                # return a tuple containing the image data, along with the width and height
                return d, i.width, i.height
        
        def get_rect(self):
                '''Returns the bounding rectangle for the sprite'''
                return Rect.from_sprite(self.s)

def collide(lhs, rhs):
        '''Checks for collision between two sprites'''
        
        # first check if the bounds overlap, no need to go further if they don't
        r1, r2 = lhs.get_rect(), rhs.get_rect()
        if r1.collides(r2):
                # calculate the overlapping area
                ri = r1.intersect(r2)
                
                # figure out the offsets of the overlapping area in each sprite
                offx1, offy1 = int(ri.x1 - r1.x1), int(ri.y1 - r1.y1)
                offx2, offy2 = int(ri.x1 - r2.x1), int(ri.y1 - r2.y1)
                
                # grab the image data
                d1, d2 = lhs.get_image(), rhs.get_image()
                
                # and cast it to something we can operate on (it starts as a string)
                p1 = cast(d1[0], POINTER(c_ubyte))
                p2 = cast(d2[0], POINTER(c_ubyte))
                
                # for each overlapping pixel, check for a collision
                for i in range(0, ri.width):
                        for j in range(0, ri.height):
                                c1 = p1[(offx1+i) + (j + offy1)*d1[1]]
                                c2 = p2[(offx2+i) + (j + offy2)*d2[1]]
                                
                                # if both pixels are non-empty, we have a collision
                                if c1 > 0 and c2 > 0:
                                        return True
        
        # no collision found
        return False
