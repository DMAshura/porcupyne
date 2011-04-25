from extramath import *
from sprite import Sprite
from collision import Collision, collide_python as collide


class Sensor(Sprite):
    def __init__(self, res):
        sensor_image = res.image_dict['Sensor.png']
        center_image(sensor_image)
        super(Sensor, self).__init__(sensor_image, x = 0, y = 0)
        self.collision = Collision(self)

    def collide(self, other):
        return collide(self.collision, other.collision)

class TinySensor(Sprite):
    def __init__(self, res):
        image = res.image_dict['TinySensor.png']
        center_image(image)
        super(TinySensor, self).__init__(image, x = 0, y = 0)
        self.collision = Collision(self)

    def collide(self, other):
        return collide(self.collision, other.collision)
