#!/usr/bin/env python 
#-*- coding: utf-8 -*-

# ====================
# | Porcupyne Engine |
# ====================
# (c) 2011
#    Bill Shillito (DM Ashura)
#    Jakub Gedeon
#    Mathias Kærlev (Mat²)
# Obviously we mean this code, not Sonic. :P  Sonic is (c) Sega and Sonic Team.
#
# This file is part of Porcupyne.
#
#    Porcupyne is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Porcupyne is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with porcupyne.  If not, see <http://www.gnu.org/licenses/>.
#
# This engine requires pyglet.  You can get it at www.pyglet.org.
#
# Special Thanks:
#   Al Murray (r0guey0shi) and Héctor Barreiro Cabrera (Damizean)
#     for their work on the Sonic Worlds and Sonic Dash engines
#     from which this code is partially ported.
#   Mercury at Sonic Retro (www.sonicretro.org)
#     for his Sonic Physics Guide
#     (http://info.sonicretro.org/Sonic_Physics_Guide)
#     from which this code is partially ported.
#   #pyglet and #python on FreeNode IRC
#     for their help and patience
#   Steve Johnson (SonicWarriorTJ)
#     for our sweet logo
#   SEGA and Sonic Team!

import math
import os
import random
import sys
import pyglet
from pyglet.window import key
'''from pyglet import resource'''
from pyglet import clock
from pyglet import font
from pyglet import gl

import pyglet.font

from pyglet.gl import (glLoadIdentity, glTranslatef, glLoadIdentity,
    glPushMatrix, glPopMatrix, glViewport, glMatrixMode, glOrtho)

from collision import Collision, collide_python as collide

import rabbyt

from sprite import Sprite

import resources

# This will be in a separate module's root namespace, but for now it is just it's own class
# This way, very little code will have to be changed when this changes
# Does not include keymap... this seems like it should go in the Controller file instead
class const(object):
    GAMEDATA_PATH = 'gamedata'
    # Game engine constants
    GAME_WIDTH = 640
    GAME_HEIGHT = 480

    FAILSAFE_AMOUNT = 20.0
    SCALE = 120

    BG_IMAGE = 'bg.jpg'
    BALL_IMAGE = 'BlueBall.png'
    SENSOR_IMAGE = 'Sensor.png'
    PLATFORM_IMAGE = 'Platform.png'

    DRAW_SENSORS = True

    SLOPE_TEST = 4 # allow 4 pixels

'''
#Load resources
resource.path.append(const.GAMEDATA_PATH)
resource.reindex()
loaded_sounds = {}
'''

# Define key mappings here so we can change them if necessary,
# either here or even in a key config menu ingame
keymap = {'up':    key.UP,
          'down':  key.DOWN,
          'left':  key.LEFT,
          'right': key.RIGHT,
          'jump':  key.Z,
          'reset': key.F,
          'size1': key.NUM_1,
          'size2': key.NUM_2,
          'size3': key.NUM_3,
          'size4': key.NUM_4,
          'size5': key.NUM_5,
          'size6': key.NUM_6,
          'gup':   key.W,
          'gdown': key.S,
          'gleft': key.A,
          'gright':key.D}
inv_keymap = dict((key,symbol) for symbol, key in keymap.iteritems())

# Utility functions
def center_image(image):
    image.anchor_x = image.width/2
    image.anchor_y = image.height/2

def play_sound(name):
    if name not in loaded_sounds:
        loaded_sounds[name] = pyglet.media.load(os.path.join(
            const.GAMEDATA_PATH, 'sounds', '%s.wav' % name), streaming = False)
    loaded_sounds[name].play()

# Sine and Cosine functions in degrees
def sin(x):
    return math.sin(math.radians(x))

def cos(x):
    return math.cos(math.radians(x))

class Game(object):
    def __init__(self):
        self.window = pyglet.window.Window(width = const.GAME_WIDTH, 
            height = const.GAME_HEIGHT, vsync = False, caption = "Porcupyne", 
            resizable = True)
        self.window.invalid = False

        # resource.path = ['.']

        res = resources.Resource()
        res.load_directory('gamedata')

        self.player1 = Ball(self, res)
        self.bg = BG(res)
        self.platforms = [
            Platform(0, -128, res),
            Platform(128, 0, res),
            Platform(-270, -50, res),
            Platform(-320, 150, res)
        ]
        self.controller = Controller(self.window, self.player1)
        self.fps_display = font.Text(pyglet.font.load('', 36, bold = True), '', 
            color=(0.5, 0.5, 0.5, 0.5), x=-300, y=-200)

        ft = font.load('Arial', 20)
        self.debug_text = [font.Text(ft, x=200, y=200),
                      font.Text(ft, x=200, y=170),
                      font.Text(ft, x=200, y=140)]
        
        # alpha channels¨
        rabbyt.set_default_attribs()

    def update(self, dt):
        self.player1.update(dt)
        self.bg.update(dt)
        
        if self.window.has_exit:
           return
        self.window.switch_to()
        self.on_draw(dt)
        self.window.flip()

    def on_draw(self, dt):
        self.window.clear()

        # This is where the code to auto-resize the window begins.

        # Set it up to draw to the whole space of the window.
        glViewport(0, 0, self.window.width, self.window.height)

        # Switch to projection matrix.
        glMatrixMode(gl.GL_PROJECTION)
        glLoadIdentity()

        # Calculate the size of our display.
        base_size = 480.0
        size_x = 0.0
        size_y = 0.0
        if (self.window.width >= self.window.height):
            size_x = base_size * (self.window.width/float(self.window.height))
            size_y = base_size
        else:
            size_x = base_size
            size_y = base_size * (self.window.height/float(self.window.width))

        # Set the orthogonal projection.
        glOrtho(-size_x/2.0, size_x/2.0, -size_y/2.0, size_y/2.0, -100, 100)

        # Switch back to model view so we can do the rest of our drawing.
        glMatrixMode(gl.GL_MODELVIEW)
        glLoadIdentity()

        # Draw stuff in the level.
        glPushMatrix()
        glTranslatef(int(-self.player1.x), int(-self.player1.y), 0.0)

        self.bg.draw()

        for platform in self.platforms:
            platform.render()

        self.player1.draw()
        if const.DRAW_SENSORS:
            for sensor in self.player1.sensors:
                sensor.render()
        
        glPopMatrix()

        # Draw HUD.
        self.fps_display.text = 'FPS: %d' % (1 / dt)
        self.fps_display.draw()

        self.debug_text[0].text = str(self.player1.flagGround)
        self.debug_text[1].text = '0'
        self.debug_text[2].text = '0'
        self.debug_text[0].draw()
        self.debug_text[1].draw()
        self.debug_text[2].draw()

class Sensor(Sprite):
    def __init__(self, res):
        sensor_image = res.image_dict[const.SENSOR_IMAGE]
        center_image(sensor_image)
        super(Sensor, self).__init__(sensor_image, x = 0, y = 0)
        self.collision = Collision(self)

    def collide(self, other):
        return collide(self.collision, other.collision)

class Platform(Sprite):
    def __init__(self, x, y, res):
        platform_image = res.image_dict[const.PLATFORM_IMAGE]
        center_image(platform_image)
        super(Platform, self).__init__(platform_image, x = x, y = y)
        self.collision = Collision(self)

class Ball(object):
    def __init__(self, game, res):
        self.ball_image = res.image_dict[const.BALL_IMAGE]
        center_image(self.ball_image)
        self.width = self.ball_image.width
        self.height = self.ball_image.height
    
        self.game = game
        self.res = res
        x = y = 200
        self.sprite = Sprite(self.ball_image, x = x, y = y)
        self.x = x
        self.y = y

        # Sensors

        self.sensor_bottom = Sensor(self.res)
        self.sensor_top = Sensor(self.res)
        self.sensor_left = Sensor(self.res)
        self.sensor_right = Sensor(self.res)
        self.sensor_ground = Sensor(self.res)
        self.sensors = [self.sensor_bottom,
                        self.sensor_top,
                        self.sensor_left,
                        self.sensor_right,
                        self.sensor_ground]

        # Values according to the Sonic Physics Guide
        
        self.acc = 0.046875 * const.SCALE
        self.frc = 0.046875 * const.SCALE
        self.dec = 0.5 * const.SCALE
        self.max = 6.0 * const.SCALE

        self.air = 0.09375 * const.SCALE
        self.grv = 0.21875 * const.SCALE
        self.maxg = 16.0 * const.SCALE

        self.jmp = 6.5 * const.SCALE
        self.jmpweak = 4.0 * const.SCALE

        # Flags

        self.flagGround = False
        self.flagAllowJump = False
        self.flagJumpNextFrame = False

        # Trig

        self.angle = 0
        self.gangle = 0

        # Movement (dh = horizontal, dv = vertical.)
        # These can be rotated using angle and gangle above.

        self.dh = 0.0
        self.dv = 0.0
        
        self.keyUp = False
        self.keyDown = False
        self.keyLeft = False
        self.keyRight = False
        self.keyJump = False


    def release_jump(self):
        self.dv = min(self.dv, self.jmpweak)
    
    def set_position(self, x = None, y = None):
        x = x or self.x
        y = y or self.y
        self.x = x
        self.y = y
        self.sprite.x = int(x)
        self.sprite.y = int(y)
        self.update_sensors()

    def handle_input(self):
        # Speed input and management
        if self.keyLeft:
            if self.dh > 0 and self.flagGround:
                self.dh -= self.dec
                if -self.dec < self.dh < 0:
                    self.dh = -self.dec
            elif self.dh > -self.max:
                if self.flagGround:
                    self.dh = max(self.dh - self.acc, -self.max)
                else:
                    self.dh = max(self.dh - self.air, -self.max)
        elif self.keyRight:
            if self.dh < 0 and self.flagGround:
                self.dh += self.dec
                if 0 < self.dh < self.dec:
                    self.dh = self.dec
            elif self.dh < self.max:
                if self.flagGround:
                    self.dh = min(self.dh + self.acc, self.max)
                else:
                    self.dh = min(self.dh + self.air, self.max)
        elif not self.keyLeft and not self.keyRight and self.flagGround:
            self.dh -= min(abs(self.dh), self.frc) * cmp(self.dh,0)

        #Jumping
        if self.flagJumpNextFrame:
            self.res.sound_dict['jump.wav'].play()
            self.dv = self.jmp
            self.flagGround = False
            self.flagAllowJump = False
            self.flagJumpNextFrame = False
        if self.keyJump and self.flagGround and self.flagAllowJump:
            self.flagJumpNextFrame = True

    def update_sensors(self):
        self.sensor_top.x = int(self.x) - sin(self.angle) * (
            self.height/2.0 - self.sensor_bottom.height/2.0)
        self.sensor_top.y = int(self.y) + cos(self.angle) * (
            self.height/2.0 - self.sensor_bottom.height/2.0)

        self.sensor_bottom.x = int(self.x) + sin(self.angle) * (
            self.height/2.0 - self.sensor_top.height/2.0)
        self.sensor_bottom.y = int(self.y) - cos(self.angle) * (
            self.height/2.0 - self.sensor_top.height/2.0)

        self.sensor_left.x = int(self.x) - cos(self.angle) * (
            self.width/2.0 - self.sensor_left.width/2.0)
        self.sensor_left.y = int(self.y) - sin(self.angle) * (
            self.width/2.0 - self.sensor_left.width/2.0)

        self.sensor_right.x = int(self.x) + cos(self.angle) * (
            self.width/2.0 - self.sensor_left.width/2.0)
        self.sensor_right.y = int(self.y) + sin(self.angle) * (
            self.width/2.0 - self.sensor_left.width/2.0)

        self.sensor_ground.x = int(self.x) + sin(self.angle) * (
            self.height/2.0 + self.sensor_ground.height/2.0)
        self.sensor_ground.y = int(self.y) - cos(self.angle) * (
            self.height/2.0 + self.sensor_ground.height/2.0)

    def perform_speed_movement(self, dt):
        collided = False
        for i in range(0, int(const.FAILSAFE_AMOUNT)):
            self.x += cos(self.angle) * self.dh/const.FAILSAFE_AMOUNT * dt
            self.y += sin(self.angle) * self.dh/const.FAILSAFE_AMOUNT * dt
            self.update_sensors()
            for platform in self.game.platforms:
                '''
                if self.sensor_bottom.collide(platform):
                    # first, try see if it's a small slope
                    for _ in xrange(const.SLOPE_TEST):
                        self.y += 1
                        self.update_sensors()
                        if not self.sensor_bottom.collide(platform):
                            break
                '''
                if (self.sensor_left.collide(platform) or 
                self.sensor_right.collide(platform)):
                    self.update_sensors()
                    while self.sensor_left.collide(platform):
                        collided = True
                        self.x += cos(self.angle)
                        self.y += sin(self.angle)
                        self.update_sensors()
                    while self.sensor_right.collide(platform):
                        collided = True
                        self.x -= cos(self.angle)
                        self.y -= sin(self.angle)
                        self.update_sensors()
            if collided:
                self.dx = 0
                break
        self.sprite.x = int(self.x)

    def perform_gravity_movement(self, dt):
        self.dv = max(self.dv - self.grv, -self.maxg)
        collided = False

        # Failsafe movement
        for i in range(0, int(const.FAILSAFE_AMOUNT)):
            self.y += cos(self.angle) * (self.dv/const.FAILSAFE_AMOUNT) * dt
            self.x -= sin(self.angle) * (self.dv/const.FAILSAFE_AMOUNT) * dt
            self.update_sensors()
            for platform in self.game.platforms:
                while self.sensor_bottom.collide(platform):
                    collided = True
                    if self.dv > 0:
                        self.y -= cos(self.angle)
                        self.x += sin(self.angle)
                    else:
                        self.y += cos(self.angle)
                        self.x -= sin(self.angle)
                    self.update_sensors()
                while self.sensor_top.collide(platform):
                    collided = True
                    if self.dv > 0:
                        self.y -= cos(self.angle)
                        self.x += sin(self.angle)
                    else:
                        self.y += cos(self.angle)
                        self.x -= sin(self.angle)
                    self.update_sensors()
            if collided:
                if self.dv < 0:
                    self.flagGround = True
                self.dv = 0
                break
        
        self.sprite.y = int(self.y)

    def perform_ground_test(self):
        for platform in self.game.platforms:
            if self.sensor_ground.collide(platform):
                return True
        self.flagGround = False
        return False

    def update(self, dt):
        if self.flagGround and not self.keyJump:
            self.flagAllowJump = True
        self.handle_input()
        self.perform_speed_movement(dt)
        if not self.flagGround or not self.perform_ground_test():
            self.perform_gravity_movement(dt)
    
    def draw(self):
        self.sprite.render()

    def key_press(self, message):
        if message == 'up':
            self.keyUp = True
        elif message == 'down':
            self.keyDown = True
        elif message == 'left':
            self.keyLeft = True
        elif message == 'right':
            self.keyRight = True
        elif message == 'jump':
            self.keyJump = True
        elif message == 'reset':
            self.set_position(100,95)
            self.dv = 0
            self.dh = 0
        elif message == 'gdown':
            self.angle = 0
        elif message == 'gright':
            self.angle = 90
        elif message == 'gup':
            self.angle = 180
        elif message == 'gleft':
            self.angle = 270

    def key_release(self, message):
        if message == 'up':
            self.keyUp = False
        elif message == 'down':
            self.keyDown = False
        elif message == 'left':
            self.keyLeft = False
        elif message == 'right':
            self.keyRight = False
        elif message == 'jump':
            self.keyJump = False
            self.release_jump()
        

class BG(pyglet.sprite.Sprite):
    def __init__(self, res):
        self.bg_image = res.image_dict[const.BG_IMAGE]
        center_image(self.bg_image)
        super(BG, self).__init__(self.bg_image, 0, 0)
        self.dx = 0

    def update(self, dt):
        self.x += self.dx * dt

class Controller:
    def __init__(self, window, player):
        window.push_handlers(on_key_press = self.handle_key_press)
        window.push_handlers(on_key_release = self.handle_key_release)
        self.player = player
        self.window = window

    def handle_key_press(self, symbol, modifiers):
        if not symbol in inv_keymap:
            return
        message = inv_keymap[symbol]
        self.player.key_press(message)
        # player2.key_press(message)

    def handle_key_release(self, symbol, modifiers):
        if not symbol in inv_keymap:
            return
        message = inv_keymap[symbol]
        self.player.key_release(message)
        # player2.key_release(message)
        #resize code        
        if message == 'size1':
            self.window.set_size(320, 240)
        elif message == 'size2':
            self.window.set_size(640, 480)
        elif message == 'size3':
            self.window.set_size(960, 720)
        elif message == 'size4':
            self.window.set_size(427, 240)
        elif message == 'size5':
            self.window.set_size(854, 480)
        elif message == 'size6':
            self.window.set_size(1280, 720)




# Temporary code to get the commit functional, this MUST BE CHANGED SOON!
if __name__ == "__main__":
    game = Game()

    pyglet.clock.schedule_interval(game.update, 1 / 60.0)
    pyglet.app.run()
