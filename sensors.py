from extramath import *
from sprite import Sprite
from collision import BoundingBox

class Sensor(Sprite):
    def __init__(self, res):
        sensor_image = res.image_dict['Sensor.png']
        center_image(sensor_image)
        super(Sensor, self).__init__(sensor_image, x = 0, y = 0)
        self.collision = BoundingBox(self)

    def collide(self, other):
        return self.collision.collide(other.collision)

class TinySensor(Sprite):
    def __init__(self, res):
        image = res.image_dict['TinySensor.png']
        center_image(image)
        super(TinySensor, self).__init__(image, x = 0, y = 0)
        self.collision = BoundingBox(self)

    def collide(self, other):
        return self.collision.collide(other.collision)