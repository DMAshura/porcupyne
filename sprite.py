from rabbyt.sprites import Sprite as RabbytSprite

class Sprite(RabbytSprite):
    @property
    def width(self):
        return self.texture.width

    @property
    def height(self):
        return self.texture.height