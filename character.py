from extramath import *
from sprite import Sprite
from collision import Collision, collide_python as collide
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

        # Sensors

        self.sensor_bottom = Sensor(self.res)
        self.sensor_top = Sensor(self.res)
        self.sensor_left = Sensor(self.res)
        self.sensor_right = Sensor(self.res)
        self.sensor_ground = Sensor(self.res)
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
        self.dec = 0.5 * const.SCALE
        self.max = 6.0 * const.SCALE

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
        # Slope factor
        '''if not self.Rolling:'''
        if self.flagGround:
            self.dh -= self.slp * sin(self.rangle)
        '''
        else:
            if cmp(self.dh,0) == cmp(sin(self.rangle)):
                self.dh -= self.ruslp * sin(self.rangle)
            elif cmp(self.dh,0) == -cmp(sin(self.rangle)):
                self.dh -= self.rdslp * sin(self.rangle)
        '''

        # Falling off walls and ceilings
        if 45 < self.rangle < 315 and abs(self.dh) < 2.5 * const.SCALE:
            self.set_gravity(self.gangle)
            self.flagFellOffWallOrCeiling = True
        
        # Speed input and management
        if self.flagAllowHorizMovement:
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

        #Air Drag
        if 0 < self.dv < 4*const.SCALE and abs(self.dh) >= 0.125:
            self.dh *= self.drg

        #Jumping
        if self.flagJumpNextFrame:
            self.res.sound_dict['jump.wav'].play()
            self.dv = self.jmp
            self.set_gravity(self.gangle)
            self.flagGround = False
            self.flagAllowJump = False
            self.flagJumpNextFrame = False
        if self.keyJump and self.flagGround and self.flagAllowJump:
            self.flagJumpNextFrame = True

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
        self.rangle = (self.angle - self.gangle) % 360

    def calculate_angle(self, angle=None):
        if angle == None:
            angle = self.angle
        slg = self.sensor_left_ground
        smg = self.sensor_middle_ground
        srg = self.sensor_right_ground

        # When this is called, the sensors should be visible.
        '''
        self.sensor_left_ground.visible = True
        self.sensor_middle_ground.visible = True
        self.sensor_right_ground.visible = True
        '''
        
        slg.x = int(self.x) - cos(angle) * (
            7*const.ANGLE_SENSOR_SCALE - slg.width/2.0)
        slg.y = int(self.y) - sin(angle) * (
            7*const.ANGLE_SENSOR_SCALE - slg.width/2.0)

        smg.x = int(self.x)
        smg.y = int(self.y)

        srg.x = int(self.x) + cos(angle) * (
            7*const.ANGLE_SENSOR_SCALE - srg.width/2.0)
        srg.y = int(self.y) + sin(angle) * (
            7*const.ANGLE_SENSOR_SCALE - srg.width/2.0)

        left_collide = False
        middle_collide = False
        right_collide = False

        for _ in range(1, const.ANGLE_STEPS * const.ANGLE_SENSOR_SCALE):
            for platform in self.game.platforms:
                if slg.collide(platform):
                    left_collide = True
                if smg.collide(platform):
                    middle_collide = True
                if srg.collide(platform):
                    right_collide = True
            if not left_collide:
                slg.x += sin(angle)
                slg.y -= cos(angle)
            if not middle_collide:
                smg.x += sin(angle)
                smg.y -= cos(angle)
            if not right_collide:
                srg.x += sin(angle)
                srg.y -= cos(angle)

        if left_collide and right_collide:
            return direction(slg, srg)
        else:
            if left_collide:
                if middle_collide:
                    return direction(slg, smg) % 360
                else:
                    return angle % 360
            elif right_collide:
                if middle_collide:
                    return direction(smg, srg)
                else:
                    return angle % 360
            else:
                return self.gangle % 360
        

    def perform_speed_movement(self, dt):
        leftcollided = False
        rightcollided = False
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
                        leftcollided = True
                        self.x += cos(self.angle)
                        self.y += sin(self.angle)
                        self.update_sensors()
                    while self.sensor_right.collide(platform):
                        rightcollided = True
                        self.x -= cos(self.angle)
                        self.y -= sin(self.angle)
                        self.update_sensors()
                while self.sensor_bottom.collide(platform):
                    self.y += cos(self.angle)
                    self.x -= sin(self.angle)
                    self.update_sensors()
            if leftcollided:
                if not self.flagGround:
                    self.catch_left_wall()
                else:
                    self.dh = 0
                break
            elif rightcollided:
                if not self.flagGround:
                    self.catch_right_wall()
                else:
                    self.dh = 0
                break
        self.sprite.x = self.x = int(self.x)
        self.sprite.y = self.y = int(self.y)

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
                    if self.dv < 0:
                        collided = True
                    self.y += cos(self.angle)
                    self.x -= sin(self.angle)
                    self.update_sensors()
                while self.sensor_top.collide(platform):
                    if self.dv > 0:
                        collided = True
                    self.y -= cos(self.angle)
                    self.x += sin(self.angle)
                    self.update_sensors()
            if collided:
                if self.dv < 0:
                    self.flagGround = True
                    if self.flagFellOffWallOrCeiling:
                        self.set_hlock(30)
                        self.flagFellOffWallOrCeiling = False
                    self.perform_landing_movement()
                elif self.dv > 0:
                    self.catch_ceiling()
                self.dv = 0
                break
        self.sprite.x = self.x = int(self.x)
        self.sprite.y = self.y = int(self.y)

    def perform_landing_movement(self):
        rangle = (self.calculate_angle() - self.gangle) % 360
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

    def catch_ceiling(self):
        rangle = (self.calculate_angle(self.gangle + 180) - self.gangle) % 360
        if 135 <= rangle <= 225:
            "Nothing extra happens!"
        if 90 <= rangle < 135 or 225 < rangle <= 270:
            self.flagGround = True
            self.angle = rangle
            self.calculate_rangle()

    def catch_left_wall(self):
        rangle = (self.calculate_angle(self.gangle + 270) - self.gangle) % 360
        if 90 < rangle < 135:
            self.flagGround = True
            self.angle = rangle
            self.calculate_rangle()
        else:
            self.dh = 0

    def catch_right_wall(self):
        rangle = (self.calculate_angle(self.gangle + 90) - self.gangle) % 360
        if 225 < rangle < 270:
            self.flagGround = True
            self.angle = rangle
            self.calculate_rangle()
        else:
            self.dh = 0

    def perform_ground_test(self):
        for platform in self.game.platforms:
            if self.sensor_ground.collide(platform):
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
        if self.flagGround:
            self.angle = self.calculate_angle()
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
