#!/usr/bin/env python
# Frozen Jam by tgfcoder <https://twitter.com/tgfcoder> licensed under CC-BY-3
# Art from Kenney.nl
import pygame
import random
from os import path

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# Game
GAME_NAME = "My Game"

# Screen
WIDTH = 360
HEIGHT = 480
FPS = 30

# Player
N_OF_LIFES = 1
SHOOT_DELAY = 300
POWERUP_TIME = 5000
# Shield Bar
BAR_LENGTH = 100
BAR_HEIGHT = 10

# Mobs
N_OF_MOBS = 15
PROB_DROP_POWERUPS = 0.9


class Pow(pygame.sprite.Sprite):
    def __init__(self, game, center):
        pygame.sprite.Sprite.__init__(self)
        self.game = game
        self.type = random.choice(['shield', 'gun'])
        self.image = self.game.loads.powerups_images[self.type]
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.speedy = 2

    def update(self):
        self.rect.y += self.speedy
        # kill if it moves off the bottom of the screen
        if self.rect.top > HEIGHT:
            self.kill()


class Explosion(pygame.sprite.Sprite):
    def __init__(self, game, center, size):
        pygame.sprite.Sprite.__init__(self)
        self.game = game
        self.size = size
        self.image = self.game.loads.explosion_anim[self.size][0]
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.frame = 0
        self.last_update = pygame.time.get_ticks()
        self.frame_rate = 50

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.frame_rate:
            self.last_update = now
            self.frame += 1
            if self.frame == len(self.game.loads.explosion_anim[self.size]):
                self.kill()
            else:
                center = self.rect.center
                self.image = self.game.loads.explosion_anim[self.size][self.frame]
                self.rect = self.image.get_rect()
                self.rect.center = center


class Mob(pygame.sprite.Sprite):
    def __init__(self, game):
        pygame.sprite.Sprite.__init__(self)
        self.game = game
        self.init_variables()

    def init_variables(self):
        self.image_orig = random.choice(self.game.loads.mobs_images)
        self.image = self.image_orig.copy()

        self.rect = self.image.get_rect()
        self.radius = int(self.rect.width * 0.85 / 2)
        # pygame.draw.circle(self.image, RED, self.rect.center, self.radius)

        self.rect.x = random.randrange(WIDTH - self.rect.width)
        self.rect.y = random.randrange(-100, -40)
        self.speedx = random.randrange(-2, 2)
        self.speedy = random.randrange(1, 8)

        self.rot = 0
        self.rot_speed = random.randrange(-8, 8)
        self.last_update = pygame.time.get_ticks()

    def rotate(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > 50:
            self.last_update = now
            # do rotation here
            self.rot = (self.rot + self.rot_speed) % 360
            old_center = self.rect.center
            self.image = pygame.transform.rotate(self.image_orig, self.rot)
            self.rect = self.image.get_rect()
            self.rect.center = old_center

    def update(self):
        self.rotate()
        self.rect.y += self.speedy
        self.rect.x += self.speedx
        if self.rect.top > HEIGHT + 10 or self.rect.right < 0 or\
                self.rect.x > WIDTH:
            self.init_variables()


class Bullet(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.game = game

        self.image = self.game.loads.bullet_image

        self.rect = self.image.get_rect()
        self.rect.bottom = y
        self.rect.centerx = x
        self.speedy = -10

        self.ratio = pygame.sprite.collide_rect_ratio(.5)

    def update(self):
        self.rect.y += self.speedy
        # kill if it moves off the top of the screen
        if self.rect.bottom < 0:
            self.kill()


class Player(pygame.sprite.Sprite):
    def __init__(self, game):
        pygame.sprite.Sprite.__init__(self)
        self.game = game

    def init_variables(self):
        self.image = self.game.loads.player_image
        self.mini_img = pygame.transform.scale(self.image, (28, 19))
        self.rect = self.image.get_rect()
        self.radius = 20
        # pygame.draw.circle(self.image, RED, self.rect.center, self.radius)

        self.rect.centerx = WIDTH / 2
        self.rect.bottom = HEIGHT - 10
        self.speedx = 0

        self.shield = 100
        self.shield_update = pygame.time.get_ticks()

        self.score = 0

        self.shoot_delay = SHOOT_DELAY
        self.left_to_shoot = SHOOT_DELAY
        self.last_shot = pygame.time.get_ticks()

        self.lives = N_OF_LIFES
        self.hidden = False
        self.hide_timer = pygame.time.get_ticks()

        self.power = 1
        self.power_time = pygame.time.get_ticks()

    def update(self):
        now = pygame.time.get_ticks()
        self.speedx = 0
        keystate = pygame.key.get_pressed()
        if keystate[pygame.K_LEFT]:
            self.speedx = -8
        if keystate[pygame.K_RIGHT]:
            self.speedx = 8
        self.rect.x += self.speedx
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
        if self.rect.left < 0:
            self.rect.left = 0
        if keystate[pygame.K_SPACE]:
            if self.left_to_shoot <= 0:
                self.shoot()
                self.last_shot = now
        self.left_to_shoot = SHOOT_DELAY - (now - self.last_shot)

        if now - self.shield_update > 1000:
            self.shield_update = now
            self.shield += 1
            self.shield = min(self.shield, 100)
        if self.shield <= 0:
            self.death_explosion =\
                Explosion(self.game, self.rect.center, 'player')
            self.game.all_sprites.add(self.death_explosion)

            self.hide()
            self.lives -= 1
            self.shield = 100

        # unhide if hidden
        if self.hidden and pygame.time.get_ticks() - self.hide_timer > 1000:
            self.hidden = False
            self.rect.centerx = WIDTH / 2
            self.rect.bottom = HEIGHT - 10

        if self.lives == 0 and not self.death_explosion.alive():
            self.game.over = True

        # timeout for powerups
        if self.power >= 2 and\
                pygame.time.get_ticks() - self.power_time > POWERUP_TIME:
            self.power -= 1
            self.power_time = pygame.time.get_ticks()

    def powerup(self):
        self.power += 1
        self.power_time = pygame.time.get_ticks()

    def hide(self):
        # hide the player temporarily
        self.hidden = True
        self.hide_timer = pygame.time.get_ticks()
        self.rect.center = (WIDTH / 2, HEIGHT + 200)

    def shoot(self):
        if self.power == 1:
            bullet = Bullet(self.game, self.rect.centerx, self.rect.top)
            self.game.all_sprites.add(bullet)
            self.game.bullets.add(bullet)
            self.game.loads.shoot_sound.play()
        else:
            bullet1 = Bullet(self.game, self.rect.left, self.rect.centery)
            bullet2 = Bullet(self.game, self.rect.right, self.rect.centery)
            self.game.all_sprites.add(bullet1)
            self.game.all_sprites.add(bullet2)
            self.game.bullets.add(bullet1)
            self.game.bullets.add(bullet2)
            self.game.loads.shoot_sound.play()


class Loads(object):
    def __init__(self, game):
        self.game = game
        self.sound()
        self.background()
        self.player()
        self.bullet()
        self.mobs()
        self.explosions()
        self.powerups()

    def sound(self):
        self.snd_dir = path.join(path.dirname(__file__), 'music')
        # pygame.mixer.init()
        pygame.mixer.music.load(path.join(
            self.snd_dir, 'tgfcoder-FrozenJam-SeamlessLoop.mp3'))
        pygame.mixer.music.set_volume(0.4)
        pygame.mixer.music.play(loops=-1)

        self.shoot_sound = pygame.mixer.Sound(path.join(self.snd_dir,
                                                        'pew.wav'))

        self.expl_sounds = []
        for snd in ['expl3.wav', 'expl6.wav']:
            self.expl_sounds.append(pygame.mixer.Sound(path.join(self.snd_dir,
                                                                 snd)))

    def background(self):
        self.image_dir = path.join(path.dirname(__file__), 'SpaceShooterRedux')
        self.image_bg_dir = path.join(self.image_dir, 'Backgrounds')
        self.image_bg = path.join(self.image_bg_dir, 'starfield.png')
        self.image_png = path.join(self.image_dir, 'PNG')
        self.background_image = pygame.image.load(self.image_bg).convert()
        self.background_rect = self.background_image.get_rect()

    def player(self):
        try:
            self.image_path = path.join(self.image_png,
                                        "playerShip1_orange.png")
            self.player_image = pygame.image.load(self.image_path).convert()
            self.player_image.set_colorkey(BLACK)  # set borders to transparent color
            self.player_image = pygame.transform.scale(self.player_image, (50, 38))

            self.mini_image = pygame.transform.scale(self.player_image, (25, 19))
            self.mini_image.set_colorkey(BLACK)
        except pygame.error:
            self.player_image = pygame.Surface((50, 40))
            self.player_image.fill(GREEN)

    def bullet(self):
        try:
            self.image_dir = path.join(self.image_png, "Lasers")
            self.image_path = path.join(self.image_dir, "laserRed16.png")
            self.bullet_image = pygame.image.load(self.image_path).convert()
            self.bullet_image.set_colorkey(BLACK)  # set borders to transparent color
        except pygame.error:
            self.bullet_image = pygame.Surface((10, 20))
            self.bullet_image.fill(YELLOW)

    def mobs(self):
        # Mobs:
        self.mobs_images = []
        self.mobs_list = ['meteorBrown_big1.png', 'meteorBrown_med1.png',
                          'meteorBrown_med1.png', 'meteorBrown_med3.png',
                          'meteorBrown_small1.png', 'meteorBrown_small2.png',
                          'meteorBrown_tiny1.png']
        for image_name in self.mobs_list:
            try:
                self.mobs_dir = path.join(self.image_png, "Meteors")
                self.mobs_path = path.join(self.mobs_dir, image_name)
                self.mobs_image = pygame.image.load(self.mobs_path).convert()
                # set borders to transparent color:
                self.mobs_image.set_colorkey(BLACK)
                # self.image = self.image_orig.copy()
            except pygame.error:
                self.mobs_image = pygame.Surface((30, 40))
                self.mobs_image.fill(RED)
            self.mobs_images.append(self.mobs_image)

    def explosions(self):
        self.explosion_anim = {}
        self.explosion_anim['lg'] = []
        self.explosion_anim['sm'] = []
        self.explosion_anim['player'] = []
        for i in range(9):
            filename = 'regularExplosion0{}.png'.format(i)
            image_dir = path.join(self.image_png, "Explosions_kenney")
            image = pygame.image.load(path.join(image_dir, filename)).convert()
            image.set_colorkey(BLACK)
            image_lg = pygame.transform.scale(image, (75, 75))
            self.explosion_anim['lg'].append(image_lg)
            image_sm = pygame.transform.scale(image, (32, 32))
            self.explosion_anim['sm'].append(image_sm)

            image_dir = path.join(self.image_png, "shmup_player_expl")
            filename = 'sonicExplosion0{}.png'.format(i)
            image = pygame.image.load(path.join(image_dir, filename)).convert()
            image.set_colorkey(BLACK)
            self.explosion_anim['player'].append(image)

    def powerups(self):
        self.powerups_images = {}
        self.powerups_dir = path.join(self.image_png, "Power-ups")
        self.powerups_images['shield'] = pygame.image.load(path.join(
            self.powerups_dir, 'shield_gold.png')).convert()
        self.powerups_images['gun'] = pygame.image.load(
            path.join(self.powerups_dir, 'bolt_gold.png')).convert()


class Game(object):
    def __init__(self):

        pygame.init()

        self.font_name = pygame.font.match_font('arial')

        self.init_all_sprites()

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(GAME_NAME)
        self.loads = Loads(self)
        # self.load_sound()
        # # Load all game graphics
        # self.load_background()
        # self.load_player()
        # self.load_mobs()
        # self.load_explosions()
        # self.load_powerups()

        self.player.init_variables()
        self.create_all_mobs()

        self.clock = pygame.time.Clock()

        self.running = True
        self.over = False
        self.loop()

    def loop(self):
        while self.running:
            if self.over:
                print "it's over?"
                self.show_go_screen()
                self.over = False
                self.init_all_sprites()
                self.player.init_variables()
                self.create_all_mobs()
                self.player.score = 0
            self.clock.tick(FPS)
            # Process input (events)
            for event in pygame.event.get():
                self.handle_common_events(event)
            # Update
            self.all_sprites.update()
            hits = pygame.sprite.spritecollide(self.player, self.mobs, True,
                                               pygame.sprite.collide_circle)
            # if hits:
            #     self.running = False
            for mob in hits:
                self.player.shield -= mob.radius * 2
                expl = Explosion(self, mob.rect.center, 'sm')
                self.all_sprites.add(expl)
                self.new_mob()
            # check to see if a bullet hit a mob
            self.bullets.ratio = pygame.sprite.collide_rect_ratio(.5)
            hits = pygame.sprite.groupcollide(self.bullets, self.mobs,
                                              True, True, self.bullets.ratio)

            for bullet, mobs in hits.items():
                for mob in mobs:
                    random.choice(self.loads.expl_sounds).play()
                    self.player.score += 100 / mob.radius
                    expl = Explosion(self, mob.rect.center, 'lg')
                    self.all_sprites.add(expl)
                    self.new_mob()
                    if random.random() > PROB_DROP_POWERUPS:
                        pow = Pow(self, mob.rect.center)
                        self.all_sprites.add(pow)
                        self.powerups.add(pow)
            # check to see if player hit a powerup
            hits = pygame.sprite.spritecollide(self.player, self.powerups, True)
            for hit in hits:
                if hit.type == 'shield':
                    self.player.shield += random.randrange(10, 30)
                    # if self.player.shield >= 100:
                    #     self.player.shield = 100
                if hit.type == 'gun':
                    self.player.powerup()

            # Render (draw)
            self.draw_graphics()

            pygame.display.flip()

        pygame.quit()

    def handle_common_events(self, event):
        try:
            self.cmd_key_down
        except AttributeError:
            self.cmd_key_down = False
        # check for closing window
        if event.type == pygame.QUIT:
            self.quit()

        if event.type == pygame.KEYDOWN:
            if event.key == 310:
                self.cmd_key_down = True
            if self.cmd_key_down and event.key == pygame.K_q:
                self.quit()

        if event.type == pygame.KEYUP:
            if event.key == 310:
                self.cmd_key_down = False

    def init_all_sprites(self):
        self.all_sprites = pygame.sprite.Group()
        # Player:
        self.player = Player(self)
        self.all_sprites.add(self.player)
        # Bullets:
        self.bullets = pygame.sprite.Group()
        # Mobs
        self.mobs = pygame.sprite.Group()
        # Power ups:
        self.powerups = pygame.sprite.Group()

    def new_mob(self):
        m = Mob(self)
        self.all_sprites.add(m)
        self.mobs.add(m)

    def create_all_mobs(self):
        for i in range(N_OF_MOBS):
            self.new_mob()

    def draw_graphics(self):
        self.screen.fill(BLACK)
        self.screen.blit(self.loads.background_image,
                         self.loads.background_rect)
        self.all_sprites.draw(self.screen)
        self.draw_text(self.screen, str(self.player.score), 18, WIDTH / 2, 10)
        # shield bar:
        self.draw_bar(self.screen, GREEN, 5, 5, self.player.shield, 100)
        # shoot bar:
        self.draw_bar(self.screen, RED, 5, 25,
                      self.player.shoot_delay - self.player.left_to_shoot,
                      self.player.shoot_delay)
        self.draw_lives(self.screen, WIDTH - 100, 5, self.player.lives,
                        self.player.mini_img)

    def draw_lives(self, surf, x, y, lives, img):
        for i in range(lives):
            img_rect = img.get_rect()
            img_rect.x = x + 30 * i
            img_rect.y = y
            surf.blit(img, img_rect)

    def draw_bar(self, surf, color, x, y, fill, max_fill=1):
        fill = float(fill)
        fill = max(fill, 0)
        fill = min(fill, max_fill)
        fill = fill / max_fill * BAR_LENGTH
        outline_rect = pygame.Rect(x, y, BAR_LENGTH, BAR_HEIGHT)
        fill_rect = pygame.Rect(x, y, fill, BAR_HEIGHT)
        pygame.draw.rect(surf, color, fill_rect)
        pygame.draw.rect(surf, WHITE, outline_rect, 2)

    def draw_text(self, surf, text, size, x, y):
        font = pygame.font.Font(self.font_name, size)
        text_surface = font.render(text, True, WHITE)
        text_rect = text_surface.get_rect()
        text_rect.midtop = (x, y)
        surf.blit(text_surface, text_rect)

    def show_go_screen(self):
        self.screen.blit(self.loads.background_image, self.loads.background_rect)
        self.draw_text(self.screen, "SHMUP!", 64, WIDTH / 2, HEIGHT / 4)
        self.draw_text(self.screen, "Arrow keys move, Space to fire", 22,
                       WIDTH / 2, HEIGHT / 2)
        self.draw_text(self.screen, "Press a key to begin", 18,
                       WIDTH / 2, HEIGHT * 3 / 4)
        pygame.display.flip()
        waiting = True
        while waiting:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                if event.type == pygame.KEYUP:
                    waiting = False

    def quit(self):
        self.running = False


Game()
