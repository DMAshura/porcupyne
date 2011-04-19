#!/usr/bin/env python 
#-*- coding: utf-8 -*-

# ====================
# | porcupyne Engine |
# ====================
# (c) 2011 Bill Shillito ("DM Ashura") and Mathias "Mat²" Kærlev
# Obviously we mean this code, not Sonic. :P  Sonic is (c) Sega and Sonic Team.
#
# Thanks to those from #pyglet on FreeNode IRC for your help!
#
# This file is part of porcupyne.
#
#    porcupyne is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    porcupyne is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with porcupyne.  If not, see <http://www.gnu.org/licenses/>.
#
# This engine requires pyglet.  You can get it at www.pyglet.org.

import math
import os
import random
import sys

import pyglet
from pyglet.window import key
from pyglet import resource
from pyglet import clock
from pyglet import font
from pyglet import gl

from pyglet.gl import (glLoadIdentity, glTranslatef, glLoadIdentity,
    glPushMatrix, glPopMatrix, glViewport, glMatrixMode, glOrtho)

from collide import *

from rabbyt.sprites import Sprite

GAMEDATA_PATH = 'gamedata'

#Load resources
resource.path.append(GAMEDATA_PATH)
resource.reindex()

GAME_WIDTH = 640
GAME_HEIGHT = 480

FAILSAFE_AMOUNT = 20.0

BG_IMAGE = 'bg.jpg'
BALL_IMAGE = 'BlueBall.png'
SENSOR_IMAGE = 'Sensor.png'
PLATFORM_IMAGE = 'Platform.png'

SLOPE_TEST = 4 # allow 4 pixels

# Define key mappings here so we can change them if necessary,
# either here or even in a key config menu ingame
keymap = {'up':    key.UP,
          'down':  key.DOWN,
          'left':  key.LEFT,
          'right': key.RIGHT,
          'jump':  key.Z,
          'size1': key.NUM_1,
          'size2': key.NUM_2,
          'size3': key.NUM_3,
          'size4': key.NUM_4,
          'size5': key.NUM_5,
          'size6': key.NUM_6}
inv_keymap = dict((key,symbol) for symbol, key in keymap.iteritems())


INPUT_DELAY = 10

input_queue = []
for _ in range(0, INPUT_DELAY):
    input_queue.append(0)

window = pyglet.window.Window(width = GAME_WIDTH, height = GAME_HEIGHT,
                              vsync = False,
                              caption = "Porcupyne",
                              resizable = False)
window.invalid = False
SCALE = 120

Player2 = None

def center_image(image):
    image.anchor_x = image.width/2
    image.anchor_y = image.height/2

loaded_sounds = {}

def play_sound(name):
    if name not in loaded_sounds:
        loaded_sounds[name] = pyglet.media.load(os.path.join(
            GAMEDATA_PATH, 'sounds', '%s.wav' % name), streaming = False)
    loaded_sounds[name].play()

class Sensor(pyglet.sprite.Sprite):
    sensor_image = resource.image(SENSOR_IMAGE)
    center_image(sensor_image)
    width = sensor_image.width
    height = sensor_image.height

    def __init__(self):
        x = 0
        y = 0

        super(Sensor, self).__init__(self.sensor_image, x, y)

        self.collision = SpriteCollision(self)

class Platform(pyglet.sprite.Sprite):
    platform_image = resource.image(PLATFORM_IMAGE)
    center_image(platform_image)
    width = platform_image.width
    height = platform_image.height

    def __init__(self, x=0, y=0):
        super(Platform, self).__init__(self.platform_image, x, y)

        self.collision = SpriteCollision(self)

class Ball(object):
    ball_image = resource.image(BALL_IMAGE)
    center_image(ball_image)
    width = ball_image.width
    height = ball_image.height
    sprite = None

    def __init__(self):
        x = y = 200
        self.sprite = Sprite(self.ball_image, x = x, y = y)
        self.x = x
        self.y = y

        # Sensors

        self.sensor_bottom = Sensor()
        self.sensors = [self.sensor_bottom]

        # Values according to the Sonic Physics Guide
        self.acc = 0.046875 * SCALE
        self.frc = 0.046875 * SCALE
        self.dec = 0.5 * SCALE
        self.max = 6.0 * SCALE

        self.air = 0.09375 * SCALE
        self.grv = 0.21875 * SCALE
        self.maxg = 16.0 * SCALE

        self.jmp = 6.5 * SCALE
        self.jmpweak = 4.0 * SCALE

        # Flags

        self.flagGround = False
        self.flagAllowJump = False
        self.flagJumpNextFrame = False

        self.dx = 0.0
        self.dy = 0.0

        self.keyUp = False
        self.keyDown = False
        self.keyLeft = False
        self.keyRight = False
        self.keyJump = False


    def release_jump(self):
        self.dy = min(self.dy, self.jmpweak)
    
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
            if self.dx > 0 and self.flagGround:
                self.dx -= self.dec
                if -self.dec < self.dx < 0:
                    self.dx = -self.dec
            elif self.dx > -self.max:
                if self.flagGround:
                    self.dx = max(self.dx - self.acc, -self.max)
                else:
                    self.dx = max(self.dx - self.air, -self.max)
        elif self.keyRight:
            if self.dx < 0 and self.flagGround:
                self.dx += self.dec
                if 0 < self.dx < self.dec:
                    self.dx = self.dec
            elif self.dx < self.max:
                if self.flagGround:
                    self.dx = min(self.dx + self.acc, self.max)
                else:
                    self.dx = min(self.dx + self.air, self.max)
        elif not self.keyLeft and not self.keyRight and self.flagGround:
            self.dx -= min(abs(self.dx), self.frc) * cmp(self.dx,0)

        #Jumping
        if self.flagJumpNextFrame:
            play_sound('jump')
            self.dy = self.jmp
            self.flagGround = False
            self.flagAllowJump = False
            self.flagJumpNextFrame = False
        if self.keyJump and self.flagGround and self.flagAllowJump:
            self.flagJumpNextFrame = True

    def update_sensors(self):
        self.sensor_bottom.x = int(self.x)
        self.sensor_bottom.y = int(self.y) - self.width/2.0 + self.sensor_bottom.width/2.0

    def perform_speed_movement(self, dt):
        collided = False
        for i in range(0, int(FAILSAFE_AMOUNT)):
            self.x += self.dx/FAILSAFE_AMOUNT * dt
            self.update_sensors()
            for platform in platforms:
                startY = self.y
                if collide(self.sensor_bottom.collision, platform.collision):
                    # first, try see if it's a small slope
                    for _ in xrange(SLOPE_TEST):
                        self.y += 1
                        self.update_sensors()
                        if not collide(self.sensor_bottom.collision, 
                                       platform.collision):
                            break
                    else:
                        self.y = startY
                        self.update_sensors()
                        while collide(self.sensor_bottom.collision, 
                                      platform.collision):
                            collided = True
                            if self.dx > 0:
                                self.x -= 1
                            else:
                                self.x += 1
                            self.update_sensors()
            if collided:
                self.dx = 0
                break
        self.sprite.x = int(self.x)

    def perform_gravity_movement(self, dt):
        self.dy = max(self.dy - self.grv, -self.maxg)
        collided = False

        # Failsafe movement
        for i in range(0, int(FAILSAFE_AMOUNT)):
            self.y += (self.dy/FAILSAFE_AMOUNT) * dt
            self.update_sensors()
            for platform in platforms:
                while collide(self.sensor_bottom.collision, platform.collision):
                    collided = True
                    if self.dy > 0:
                        self.y -= 1
                    else:
                        self.y += 1
                    self.update_sensors()
            if collided:
                self.flagGround = True
                self.dy = 0
                break
        
        self.sprite.y = int(self.y)

    def update(self, dt):
        if self.flagGround and not self.keyJump:
            self.flagAllowJump = True
        self.handle_input()
        self.perform_speed_movement(dt)
        if not self.flagGround:
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
    bg_image = resource.image(BG_IMAGE)
    center_image(bg_image)
    width = bg_image.width
    height = bg_image.height

    def __init__(self):
        x = 0
        y = 0
        super(BG, self).__init__(self.bg_image, x, y)
        self.dx = 0

    def update(self, dt):
        self.x += self.dx * dt


class Controller:
    def __init__(self):
        window.push_handlers(on_key_press = self.handle_key_press)
        window.push_handlers(on_key_release = self.handle_key_release)

    def handle_key_press(self, symbol, modifiers):
        if not symbol in inv_keymap:
            return
        message = inv_keymap[symbol]
        myball.key_press(message)
        # player2.key_press(message)

    def handle_key_release(self, symbol, modifiers):
        if not symbol in inv_keymap:
            return
        message = inv_keymap[symbol]
        myball.key_release(message)
        # player2.key_release(message)
        #resize code        
        if message == 'size1':
            window.set_size(320, 240)
        elif message == 'size2':
            window.set_size(640, 480)
        elif message == 'size3':
            window.set_size(960, 720)
        elif message == 'size4':
            window.set_size(427, 240)
        elif message == 'size5':
            window.set_size(854, 480)
        elif message == 'size6':
            window.set_size(1280, 720)


def update(dt):
    myball.update(dt)

    mybg.update(dt)
    
    if window.has_exit:
        return
    window.switch_to()
    on_draw(dt)
    window.flip()

def on_draw(dt):
    window.clear()

    # This is where the code to auto-resize the window begins.

    # Set it up to draw to the whole space of the window.
    glViewport(0, 0, window.width, window.height)

    # Switch to projection matrix.
    glMatrixMode(gl.GL_PROJECTION)
    glLoadIdentity()

    # Calculate the size of our display.
    base_size = 480.0
    size_x = 0.0
    size_y = 0.0
    if (window.width >= window.height):
        size_x = base_size * (window.width/float(window.height))
        size_y = base_size
    else:
        size_x = base_size
        size_y = base_size * (window.height/float(window.width))

    # Set the orthogonal projection.
    glOrtho(-size_x/2.0, size_x/2.0, -size_y/2.0, size_y/2.0, -100, 100)

    # Switch back to model view so we can do the rest of our drawing.
    glMatrixMode(gl.GL_MODELVIEW)
    glLoadIdentity()

    # I can eventually use this to change the camera. 
    #glTranslatef(window.width/window.scale/2, window.height/window.scale/2, 0.0)
    glPushMatrix()
    glTranslatef(int(-myball.x), int(-myball.y), 0.0)
    mybg.draw()
    myball.draw()
    for sensor in myball.sensors:
        sensor.draw()
    for platform in platforms:
        platform.draw()
    
    glPopMatrix()

    fps_display.text = '%d' % (1 / dt)
    fps_display.draw()

    debug_text.text = str(myball.flagGround)
    debug_text.draw()

myball = Ball()
mybg = BG()
platforms = [
    Platform(0, -128),
    Platform(128, 0)
]
mycontroller = Controller()

import pyglet.font
fps_display = pyglet.font.Text(pyglet.font.load('', 36, bold = True), '', 
    color=(0.5, 0.5, 0.5, 0.5), x = 10, y = 10)

ft = font.load('Arial', 20)
debug_text = font.Text(ft, y=-200)

pyglet.clock.schedule_interval(update, 1 / 60.0)
pyglet.app.run()
