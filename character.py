from extramath import *
from sprite import Sprite
from sensors import Sensor, TinySensor
from constants import const

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

        # State Machine

        self.state = "Stopped"

        # Sensors

        self.sensor_bottom = Sensor(self.res)
        self.sensor_top = Sensor(self.res)
        self.sensor_left = Sensor(self.res)
        self.sensor_right = Sensor(self.res)
        self.sensor_ground = Sensor(self.res)
        self.sensor_ground.red = 0.5
        self.sensor_ground.alpha = 0.5
        self.sensor_left_ground = TinySensor(self.res)
        self.sensor_middle_ground = TinySensor(self.res)
        self.sensor_right_ground = TinySensor(self.res)
        self.sensors = [self.sensor_bottom,
                        self.sensor_top,
                        self.sensor_left,
                        self.sensor_right,
                        self.sensor_ground,
                        self.sensor_left_ground,
                        self.sensor_middle_ground,
                        self.sensor_right_ground]

        # Values according to the Sonic Physics Guide
        
        self.acc = 0.046875 * const.SCALE
        self.frc = 0.046875 * const.SCALE
        self.rfrc = 0.0234375 * const.SCALE
        self.dec = 0.5 * const.SCALE
        self.max = 6.0 * const.SCALE

        self.rol = 1.03125 * const.SCALE

        self.slp = 0.125 * const.SCALE
        self.ruslp = 0.078125 * const.SCALE
        self.rdslp = 0.3125 * const.SCALE

        self.air = 0.09375 * const.SCALE
        self.grv = 0.21875 * const.SCALE
        self.maxg = 16.0 * const.SCALE

        self.drg = 0.96875

        self.jmp = 6.5 * const.SCALE
        self.jmpweak = 4.0 * const.SCALE

        # Flags

        self.flagGround = False
        self.flagAllowJump = False
        self.flagAllowHorizMovement = True
        self.flagAllowVertMovement = True
        self.flagJumpNextFrame = False
        self.flagFellOffWallOrCeiling = False

        # Trig

        self.angle = 0.0
        self.gangle = 0.0
        self.rangle = 0.0

        # Movement (dh = horizontal, dv = vertical.)
        # These can be rotated using angle and gangle above.

        self.dh = 0.0
        self.dv = 0.0
        
        self.keyUp = False
        self.keyDown = False
        self.keyLeft = False
        self.keyRight = False
        self.keyJump = False

        # Control lock timers
        self.hlock = 0

    def play_sound(self, string):
        self.res.sound_dict[string].play()

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

    def handle_physics(self):
        # See if rolling
        if (abs(self.dh) >= self.rol):
            if (self.keyDown and self.flagGround and self.state != "Rolling"):
                self.state = "Rolling"
                self.play_sound('spin.wav')
                print "Rolling!"
        
        # Slope factor
        if self.state != "Rolling":
            if self.flagGround:
                self.dh -= self.slp * sin(self.rangle)
        else:
            if cmp(self.dh,0) == cmp(sin(self.rangle),0):
                self.dh -= self.ruslp * sin(self.rangle)
            elif cmp(self.dh,0) == -cmp(sin(self.rangle),0) or self.dh == 0:
                self.dh -= self.rdslp * sin(self.rangle)

        # Falling off walls and ceilings
        if 45 < self.rangle < 315 and abs(self.dh) < 2.5 * const.SCALE:
            self.set_gravity(self.gangle)
            self.flagFellOffWallOrCeiling = True

        if self.state == "Rolling" and self.dh == 0 and not self.keyDown:
            self.state = "Stopped"
            print "Stopped!"
        
        # Speed input and management
        if self.flagAllowHorizMovement:
            if self.keyLeft:
                if self.dh > 0 and self.flagGround:
                    # Decelerate
                    self.dh -= self.dec
                    if -self.dec < self.dh < 0:
                        self.dh = -self.dec
                elif self.dh > -self.max and self.state != "Rolling":
                    # Accelerate
                    if self.flagGround:
                        self.dh = max(self.dh - self.acc, -self.max)
                    else:
                        self.dh = max(self.dh - self.air, -self.max)
            elif self.keyRight:
                if self.dh < 0 and self.flagGround:
                    # Decelerate
                    self.dh += self.dec
                    if 0 < self.dh < self.dec:
                        self.dh = self.dec
                elif self.dh < self.max and self.state != "Rolling":
                    # Accelerate
                    if self.flagGround:
                        self.dh = min(self.dh + self.acc, self.max)
                    else:
                        self.dh = min(self.dh + self.air, self.max)
            elif not self.keyLeft and not self.keyRight and self.flagGround:
                if self.state == "Rolling":
                    self.dh -= min(abs(self.dh), self.rfrc) * cmp(self.dh,0)
                else:
                    self.dh -= min(abs(self.dh), self.frc) * cmp(self.dh,0)

        #Air Drag
        if 0 < self.dv < 4*const.SCALE and abs(self.dh) >= 0.125:
            self.dh *= self.drg

        #Jumping
        if self.flagJumpNextFrame:
            self.play_sound('jump.wav')
            self.dv = self.jmp
            self.set_gravity(self.gangle)
            self.state = "Jumping"
            self.flagGround = False
            self.flagAllowJump = False
            self.flagJumpNextFrame = False
        if self.keyJump and self.flagGround and self.flagAllowJump:
            self.flagJumpNextFrame = True

    def calculate_state(self):
        if self.flagGround:
            if self.state != "Rolling":
                if self.dh == 0:
                    self.state = "Stopped"
                elif 0 < abs(self.dh) < self.max:
                    self.state = "Walking"
                elif abs(self.dh) >= self.max:
                    self.state = "Running"
        else:
            if self.state != "Jumping":
                self.state = "Falling"

    def set_gravity(self, gangle):
        _ = rotate_basis(self.dh, self.dv, self.angle, gangle)
        self.dh = _[0]
        self.dv = _[1]
        self.angle = self.gangle = gangle

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

    def calculate_rangle(self):
        self.rangle = (self.angle - self.gangle)

    def calculate_angle(self, colliding_line):
        if colliding_line is None:
            return self.gangle
        
        x1, y1, x2, y2 = colliding_line
        return direction(x2, y2, x1, y1)

    def perform_speed_movement(self, dt):
        leftcollided = False
        rightcollided = False
        for i in range(0, int(const.FAILSAFE_AMOUNT)):
            self.x += cos(self.angle) * self.dh/const.FAILSAFE_AMOUNT * dt
            self.y += sin(self.angle) * self.dh/const.FAILSAFE_AMOUNT * dt
            self.update_sensors()
            for platform in self.game.platforms:
                colliding_line = None
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
                        colliding_line = self.sensor_left.collide(platform)[1]
                        leftcollided = True
                        self.x += cos(self.angle)
                        self.y += sin(self.angle)
                        self.update_sensors()
                    while self.sensor_right.collide(platform):
                        colliding_line = self.sensor_right.collide(platform)[1]
                        rightcollided = True
                        self.x -= cos(self.angle)
                        self.y -= sin(self.angle)
                        self.update_sensors()

                while self.sensor_bottom.collide(platform):
                    colliding_line = self.sensor_bottom.collide(platform)[1]
                    self.y += cos(self.angle)
                    self.x -= sin(self.angle)
                    self.update_sensors()
            if leftcollided:
                if not self.flagGround:
                    self.catch_left_wall(colliding_line)
                else:
                    self.dh = 0
                break
            elif rightcollided:
                if not self.flagGround:
                    self.catch_right_wall(colliding_line)
                else:
                    self.dh = 0
                break
            elif colliding_line is not None:
                self.angle = self.calculate_angle(colliding_line)
        self.sprite.x = int(self.x)
        self.sprite.y = int(self.y)

    def perform_gravity_movement(self, dt):
        self.dv = max(self.dv - self.grv, -self.maxg)
        collided = False
        colliding_line = None
        
        y_speed = cos(self.angle)
        x_speed = sin(self.angle)
        
        # Failsafe movement
        for i in range(0, int(const.FAILSAFE_AMOUNT)):
            self.y += y_speed * (self.dv/const.FAILSAFE_AMOUNT) * dt
            self.x -= x_speed * (self.dv/const.FAILSAFE_AMOUNT) * dt
            self.update_sensors()
            for platform in self.game.platforms:
                while self.sensor_bottom.collide(platform):
                    if self.dv < 0:
                        collided = True
                        colliding_line = self.sensor_bottom.collide(platform)[1]
                    self.y += y_speed
                    self.x -= x_speed
                    self.update_sensors()
                while self.sensor_top.collide(platform):
                    if self.dv > 0:
                        collided = True
                        colliding_line = self.sensor_top.collide(platform)[1]
                    self.y -= y_speed
                    self.x += x_speed
                    self.update_sensors()
            if collided:
                if self.dv < 0:
                    self.flagGround = True
                    if self.flagFellOffWallOrCeiling:
                        self.set_hlock(30)
                        self.flagFellOffWallOrCeiling = False
                    self.angle = self.calculate_angle(colliding_line)
                    self.perform_landing_movement(colliding_line)
                elif self.dv > 0:
                    self.catch_ceiling(colliding_line)
                self.dv = 0
                break
        self.sprite.x = self.x = int(self.x)
        self.sprite.y = self.y = int(self.y)

    def perform_landing_movement(self, colliding_line):
        rangle = (self.calculate_angle(colliding_line) - self.gangle)
        if 0 <= rangle < 22.5 or 337.5 < rangle < 360:
            "Nothing extra happens!"
        elif 22.5 <= rangle < 45 or 315 < rangle <= 337.5:
            if abs(self.dh) > abs(self.dv):
                "Nothing extra happens!"
            else:
                self.dh = -self.dv * 0.5 * cmp(cos(rangle),1)
        elif 45 <= rangle < 90 or 270 < rangle <= 315:
            if abs(self.dh) > abs(self.dv):
                "Nothing extra happens!"
            else:
                self.dh = -self.dv * cmp(cos(rangle),1)

    def catch_ceiling(self, colliding_line):
        rangle = (self.calculate_angle(colliding_line) - self.gangle) % 360
        if 135 <= rangle <= 225:
            "Nothing extra happens!"
        if 90 <= rangle < 135 or 225 < rangle <= 270:
            self.flagGround = True
            self.angle = rangle
            self.calculate_rangle()

    def catch_left_wall(self, colliding_line):
        rangle = (self.calculate_angle(colliding_line) - self.gangle) % 360
        if 90 < rangle < 135:
            self.flagGround = True
            self.angle = rangle
            self.calculate_rangle()
        else:
            self.dh = 0

    def catch_right_wall(self, colliding_line):
        rangle = (self.calculate_angle(colliding_line) - self.gangle)
        if 225 < rangle < 270:
            self.flagGround = True
            self.angle = rangle
            self.calculate_rangle()
        else:
            self.dh = 0

    def perform_ground_test(self):
        for platform in self.game.platforms:
            collision = self.sensor_ground.collide(platform)
            if collision is not None:
                angle = self.calculate_angle(collision[1])
                if angle != self.angle and angle != 90:
                    return False
                return True
        self.flagGround = False
        self.set_gravity(self.gangle)
        return False

    def update(self, dt):
        self.update_lock_timers(dt)
        if self.flagGround:
            if not self.keyJump:
                self.flagAllowJump = True
        else:
            # I'd like to have the sensors be invisible when not on the ground.
            '''
            self.sensor_left_ground.visible = False
            self.sensor_middle_ground.visible = False
            self.sensor_right_ground.visible = False
            '''
        self.handle_physics()
        self.perform_speed_movement(dt)
        if not self.flagGround or not self.perform_ground_test():
            self.perform_gravity_movement(dt)
        self.calculate_state()
        self.calculate_rangle()

    def update_lock_timers(self, dt):
        if self.hlock > 0:
            self.hlock = max(self.hlock - 60 * dt, 0)
        if self.hlock == 0:
            self.flagAllowHorizMovement = True

    def set_hlock(self, frames):
        self.hlock = frames
        self.flagAllowHorizMovement = False
    
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
            self.set_position(100,96)
            self.dv = 0
            self.dh = 0
            self.set_gravity(0.0)
        elif message == 'gdown':
            self.set_gravity(0.0)
        elif message == 'gright':
            self.set_gravity(90.0)
        elif message == 'gup':
            self.set_gravity(180.0)
        elif message == 'gleft':
            self.set_gravity(270.0)
        elif message == 'hlock':
            self.set_hlock(30)

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
