#!/usr/bin/env python
from __future__ import division
import pygame, pygame.gfxdraw
import random
import time
import numpy as np
from collections import deque

WHITE = (255, 255, 255)

pygame.init()
pygame.mixer.init()
popsound = pygame.mixer.Sound('media/sounds/202230__deraj__pop-sound-clipped.wav')
spawnsound = pygame.mixer.Sound('media/sounds/104950__glaneur-de-sons__bubbles-2-clipped.wav')
thudsound = pygame.mixer.Sound('media/sounds/215162__otisjames__thud-clipped.wav')
slow1sound = pygame.mixer.Sound('media/sounds/109213__timbre__similar-to-tape-slowing-to-stop-1.wav')
speed1sound = pygame.mixer.Sound('media/sounds/109213__timbre__similar-to-tape-slowing-to-stop-1-rev.wav')
levelupsound = pygame.mixer.Sound('media/sounds/76234__jivatma07__level-up-3note2.wav')

background = pygame.image.load('media/backgrounds/fudge.jpg')

class Signal(object):
    def __init__(self, *args):
        self.connections = []

    def emit(self, *args):
        for func in self.connections:
            func.__call__(*args)

    def connect(self, func):
        self.connections.append(func)

class Bubble(pygame.sprite.Sprite):
    SPEED_MULTIPLIER = 1.0
    BUBBLE_IMG = pygame.image.load('media/sprites/bubble.png')
    MIN_SPEED = 5
    MAX_SPEED = 100
    def __init__(self, side, px=0, py=0):
 
        super(Bubble, self).__init__()

        self.is_popped = False

        self.bubble_popped = Signal(tuple, float)

        self.direction = np.random.rand()*np.pi*2 
        self.speed = np.random.randint(Bubble.MIN_SPEED,Bubble.MAX_SPEED)

        self.image = pygame.transform.scale(Bubble.BUBBLE_IMG.copy(), [side, side]).convert_alpha()

        self.side = side
        self.rect = self.image.get_rect()
        self.rect.x = px
        self.rect.y = py

        self.true_x = px
        self.true_y = py

    def true_speed(self):
        return int(Bubble.SPEED_MULTIPLIER * self.speed)
 
    def update(self, dt):
        if not self.is_popped:

            dx = self.true_speed() * dt * np.cos(self.direction)
            dy = self.true_speed() * dt * np.sin(self.direction)

            # prevent bubbles from getting stuck
            if dx + dy == 0:
                dx = 1

            # maintain true position so differences < 0.5 don't get the bubble stuck
            self.true_x += dx
            self.true_y += dy

            self.rect.x = np.round(self.true_x)
            self.rect.y = np.round(self.true_y)


        else:
            font = pygame.font.Font(None, 36)
            text = font.render(str(self.score()), False, (92,150,255))
            self.image.blit(text, [self.side/2-text.get_width()/2, self.side/2-text.get_height()/2])
            self.image.set_alpha(self.image.get_alpha() - 255*dt*2)
            if self.image.get_alpha() <= 0:
                self.kill()

        if not pygame.display.get_surface().get_rect().contains(self.rect):
            self.kill()

    def clicked(self, pos):
        return self.rect.collidepoint(pos)

    def hit(self, pos):
        if not self.is_popped:
            self.is_popped = True
            self.show_score()
            popsound.play()
            self.bubble_popped.emit(pos, pygame.time.get_ticks())

    def score(self):
        return max(int(self.speed/Bubble.MAX_SPEED*10) + int((75-self.side)/10), 1)

    def show_score(self):
        self.image = pygame.Surface([self.side, self.side])
        self.image.fill(WHITE)
        self.image.set_colorkey(WHITE)
        self.image.set_alpha(255)

class BubbleGame(object):
    screen_width = 1024
    screen_height = 681
    UPDATE_BONUS = 1
    POWERUP_DURATION = 5000
    BONUS_THRESHOLD = 0.5

    def __init__(self):
        self.done = False

        self.bubble_group = pygame.sprite.Group()         
        self.all_sprites_list = pygame.sprite.Group()
 
        self.clock = pygame.time.Clock()
         
        self.score = 0
        self.font = pygame.font.Font(None, 36)

        self.screen = pygame.display.set_mode([self.screen_width, self.screen_height])

        self.movement = Signal(tuple, tuple, float, float, float)

        self.click_history = deque([], 2)

        self.last_hit_time = 0

        self.powerup_time = 0
        self.in_powerup = False

        self.bonus = 0

        self.level = 1

        for i in range(50):
            self.spawn_bubble()

    def level_from_score(self, score):
        return int(np.floor((score + 20) ** 0.24) - 1)

    def spawn_bubble(self):
        sprite = Bubble(random.randrange(20,100), random.randrange(self.screen_width), random.randrange(self.screen_height))
        # sprite.bubble_popped.connect(self.bubble_clicked)
        self.bubble_group.add(sprite)
        self.all_sprites_list.add(sprite)
        return sprite

    def maybe_spawn_bubble(self):
        if not len(self.bubble_group) or np.random.rand()/5 < 1.0/len(self.bubble_group):
            self.spawn_bubble()
            spawnsound.play()
            return True

    def update_history(self, pos, side, speed, direction):
        self.click_history.append((pos, side, speed, direction, pygame.time.get_ticks()))
        if len(self.click_history) == self.click_history.maxlen:
            self.movement.emit(
                self.click_history[0][0],
                pos,
                side,
                speed,
                direction,
                (self.click_history[1][4] - self.click_history[0][4]) / 1000
            )

    def levelup(self, level):
        levelupsound.play()

    def update_level(self):
        newlevel = max(self.level, self.level_from_score(self.score))
        if newlevel > self.level:
            self.level = newlevel
            self.levelup(newlevel)

        text = self.font.render('Level: %s' % self.level, True, (0, 255, 0))
        self.screen.blit(text, [5, 0])

    def update_score(self, delta):
        self.score += delta
        text = self.font.render('Score: %s' % self.score, True, (0, 255, 0))
        self.screen.blit(text, [5, text.get_height()+5])

    def update_bonus(self):
        self.set_bonus(self.bonus)

    def set_bonus(self, bonus):
        if not self.in_powerup and bonus > self.bonus and bonus > BubbleGame.BONUS_THRESHOLD:
            self.powerup(1)
        self.bonus = bonus
        text = self.font.render('Bonus: %s' % self.bonus, True, (0,255,0))
        self.screen.blit(text, [self.screen_width - text.get_width() - 5, 0])

    def bonus_attrition(self):
        now = pygame.time.get_ticks()
        if now - self.last_hit_time > 1000:
            self.bonus = max(0, self.bonus - 0.1)
        self.set_bonus(self.bonus)

    def powerup(self, level):
        self.in_powerup = True
        slow1sound.play()
        self.powerup_time = pygame.time.get_ticks()
        Bubble.SPEED_MULTIPLIER = 0.5

    def check_powerup_complete(self):
        if self.in_powerup and (pygame.time.get_ticks() - self.powerup_time > BubbleGame.POWERUP_DURATION):
            self.in_powerup = False
            self.powerup_time = 0
            Bubble.SPEED_MULTIPLIER = 1.0
            speed1sound.play()
            self.bonus = 0

    def run(self):
        pygame.time.set_timer(BubbleGame.UPDATE_BONUS, 1000)
        self.all_sprites_list.draw(self.screen)
        while not self.done:
            dt = 1/self.clock.tick(30)
            for event in pygame.event.get(): 
                if event.type == pygame.QUIT: 
                    self.done = True
                elif event.type == pygame.MOUSEBUTTONUP:
                    pos = pygame.mouse.get_pos()
                    clicked_objs = [s for s in self.bubble_group if s.clicked(pos)]
                    for s in clicked_objs:
                        s.hit(pos)
                        self.update_score(s.score())
                        self.set_bonus(self.bonus + 0.1)
                    if clicked_objs:
                        self.update_history(pos, s.side, s.speed, s.direction)
                        self.last_hit_time = pygame.time.get_ticks()
                    else:
                        self.update_score(-1)
                        thudsound.play()
                elif event.type == BubbleGame.UPDATE_BONUS:
                    self.bonus_attrition()
                    self.check_powerup_complete()

            self.screen.blit(background, self.screen.get_rect())
         
            self.maybe_spawn_bubble()

            self.all_sprites_list.update(dt)
            self.all_sprites_list.draw(self.screen)    
            self.update_bonus()
            self.update_level()
            self.update_score(0)
            # Go ahead and update the screen with what we've drawn.
            pygame.display.flip()
         
        pygame.quit()

from math import hypot
def gather_data(*args):
    d = hypot(*np.array(args[0])-args[1])
    print d, args[5], args[2]

if __name__ == '__main__':
    game = BubbleGame()
    game.movement.connect(gather_data)
    game.run()
