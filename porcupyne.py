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
    glPushMatrix, glPopMatrix, glViewport, glMatrixMode, glOrtho,
    glBegin, glEnd, GL_POLYGON, glVertex2f, glEnable, glHint, 
    GL_LINE_SMOOTH_HINT, GL_NICEST, GL_LINE_SMOOTH)

from collision import StaticPolygon, BoundingBox

import rabbyt

from sprite import Sprite

import resources
from character import Ball
from constants import const
from extramath import *

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
          'gright':key.D,
          'hlock': key.L}
inv_keymap = dict((key,symbol) for symbol, key in keymap.iteritems())

# Utility functions
def play_sound(name):
    if name not in loaded_sounds:
        loaded_sounds[name] = pyglet.media.load(os.path.join(
            const.GAMEDATA_PATH, 'sounds', '%s.wav' % name), streaming = False)
    loaded_sounds[name].play()

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
        platform_width = 200
        platform_height = 96
        def get_points(x, y):
            x -= platform_width / 2.0
            y -= platform_height / 2.0
            return ((
                (x, y), 
                (x, y + platform_height), 
                (x + platform_width, y + platform_height),
                (x + platform_width, y)))

        self.platforms = [
            Platform(get_points(0, -128), res),
            Platform(get_points(128, 0), res),
            Platform(get_points(-270, -50), res),
            Platform(get_points(-320, 150), res),
            Platform((
                (225, 48), (400, 160), (400, 48)
                ), res)
        ]
        self.controller = Controller(self.window, self.player1)
        self.fps_display = font.Text(pyglet.font.load('', 18, bold = True), '', 
            color=(0.5, 0.5, 0.5, 0.5), x=-150, y=-100)

        ft = font.load('Arial', 10)
        color = (0, 0, 0, 1)
        self.debug_text = [font.Text(ft, x=-150, y=100, color = color),
                      font.Text(ft, x=-150, y=85, color = color),
                      font.Text(ft, x=-150, y=70, color = color)]
        
        # alpha channels¨
        rabbyt.set_default_attribs()
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

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
        base_size = 240.0
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

        self.debug_text[0].text = str(int(self.player1.hlock))
        self.debug_text[1].text = str(self.player1.state)
        self.debug_text[2].text = str(self.player1.rangle)
        self.debug_text[0].draw()
        self.debug_text[1].draw()
        self.debug_text[2].draw()

class Platform(object):
    def __init__(self, points, res):
        self.points = points
        self.collision = StaticPolygon(points)
    
    def render(self):
        glBegin(GL_POLYGON)
        for x, y in self.points:
            glVertex2f(x, y)
        glEnd()

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
