#!/usr/bin/env python 
#-*- coding: utf-8 -*-

# ====================
# | porcupyne Engine |
# ====================
# (c) 2011 Bill Shillito ("DM Ashura") and Mathias "Mat²" Kærlev
# Obviously we mean this code, not Sonic. :P  Sonic is (c) Sega and Sonic Team.)
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

#Load resources
resource.path.append('gamedata')
resource.reindex()

GAME_WIDTH = 640
GAME_HEIGHT = 480

GRAVITY = True

FAILSAFE_AMOUNT = 20.0

BG_IMAGE = 'bg.jpg'
BALL_IMAGE = 'BlueBall.png'
SENSOR_IMAGE = 'Sensor.png'
PLATFORM_IMAGE = 'Platform.png'

window = pyglet.window.Window(width = GAME_WIDTH, height = GAME_HEIGHT,
                              vsync = True,
                              caption = "Sonic Gemini derp test!",
                              resizable = False)
SCALE = 120

def center_image(image):
    image.anchor_x = image.width/2
    image.anchor_y = image.height/2

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

class Ball(pyglet.sprite.Sprite):
    ball_image = resource.image(BALL_IMAGE)
    center_image(ball_image)
    width = ball_image.width
    height = ball_image.height

    def __init__(self):
        x = 0
        y = 0

        super(Ball, self).__init__(self.ball_image, x, y)

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

        window.push_handlers(on_key_release = self.key_released)

    def key_released(self, symbol, modifiers):
        if symbol == key.Z:
            self.release_jump()

    def release_jump(self):
        self.dy = min(self.dy, self.jmpweak)

    def handle_input(self):
        # Speed input and management
        if keys[key.LEFT]:
            if self.dx > 0 and self.flagGround:
                self.dx -= self.dec
                if -self.dec < self.dx < 0:
                    self.dx = -self.dec
            elif self.dx > -self.max:
                if self.flagGround:
                    self.dx = max(self.dx - self.acc, -self.max)
                else:
                    self.dx = max(self.dx - self.air, -self.max)
        elif keys[key.RIGHT]:
            if self.dx < 0 and self.flagGround:
                self.dx += self.dec
                if 0 < self.dx < self.dec:
                    self.dx = self.dec
            elif self.dx < self.max:
                if self.flagGround:
                    self.dx = min(self.dx + self.acc, self.max)
                else:
                    self.dx = min(self.dx + self.air, self.max)
        elif not keys[key.RIGHT] and not keys[key.LEFT] and self.flagGround:
            self.dx -= min(abs(self.dx), self.frc) * cmp(self.dx,0)

        # Y control for now because I haven't implemented gravity yet.
        if GRAVITY:
            "stuff"
        else:
            if keys[key.UP] and self.dy < self.max:
                self.dy += self.acc
            if keys[key.DOWN] and self.dy > -self.max:
                self.dy -= self.acc
            if not keys[key.UP] and not keys[key.DOWN]:
                self.dy -= min(abs(self.dy), self.frc) * cmp(self.dy,0)

        # Quickly stop downward velocity for debug
        if keys[key.H]:
            self.dy = 0
        if self.flagJumpNextFrame:
            self.dy = self.jmp
            self.flagGround = False
            self.flagAllowJump = False
            self.flagJumpNextFrame = False
        if keys[key.Z] and self.flagGround and self.flagAllowJump:
            self.flagJumpNextFrame = True

    def update_sensors(self):
        self.sensor_bottom.x = self.x
        self.sensor_bottom.y = self.y - self.width/2.0 + self.sensor_bottom.width/2.0

    def perform_speed_movement(self, dt):
        self.x += self.dx * dt

    def perform_gravity_movement(self, dt):
        if not self.flagGround:
            self.dy = max(self.dy - self.grv, -self.maxg)

        Collided = False

        # Failsafe movement
        for i in range(0, int(FAILSAFE_AMOUNT)):
            self.y += self.dy/FAILSAFE_AMOUNT * dt
            self.update_sensors()
            if collide(self.sensor_bottom.collision, myplatform.collision):
                while collide(self.sensor_bottom.collision, myplatform.collision):
                    self.y += 1
                    self.update_sensors()
                Collided = True
            if Collided:
                self.flagGround = True
                self.dy = 0
                break
        '''self.y += self.dy * dt'''

    def update(self, dt):
        if self.flagGround and not keys[key.Z]:
            self.flagAllowJump = True
        print (self.flagGround, not keys[key.Z], self.flagAllowJump)
        self.handle_input()
        self.perform_speed_movement(dt)
        self.perform_gravity_movement(dt)

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

@window.event
def on_key_press(symbol, modifiers):
    global GRAVITY
    if symbol == key.ESCAPE:
        window_has_exit = True
    elif symbol == key.NUM_1:
        window.set_size(320, 240)
    elif symbol == key.NUM_2:
        window.set_size(640, 480)
    elif symbol == key.NUM_3:
        window.set_size(960, 720)
    elif symbol == key.NUM_4:
        window.set_size(427, 240)
    elif symbol == key.NUM_5:
        window.set_size(854, 480)
    elif symbol == key.NUM_6:
        window.set_size(1280, 720)
    elif symbol == key.G:
        GRAVITY = not GRAVITY
    elif symbol == key.H:
        GRAVITY = False
    elif symbol == key.F:
        myball.flagGround = not myball.flagGround

keys = key.KeyStateHandler()
window.push_handlers(keys)

def update(dt):
    myball.update(dt)
    mybg.update(dt)

@window.event
def on_draw():
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
    #glPushMatrix()
    #glTranslatef(myball.dx, myball.dy, 0.0)
    #glPopMatrix()
    mybg.draw()
    myball.draw()
    for sensor in myball.sensors:
        sensor.draw()
    myplatform.draw()

    fps_text.text = ("fps: %d") % (clock.get_fps())
    fps_text.draw()

    colliding_text.text = str(myball.dy / SCALE)
    colliding_text.draw()

myball = Ball()
mybg = BG()
myplatform = Platform(0, -128)

ft = font.load('Arial',20)
fps_text = font.Text(ft, y=10)
colliding_text = font.Text(ft, y=-200)

pyglet.clock.schedule(update)
pyglet.clock.set_fps_limit(60)
pyglet.app.run()
