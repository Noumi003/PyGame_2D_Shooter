import pygame
from pygame import mixer
import os
import random
import csv
import button

mixer.init()
pygame.init()

# Game Window
screen_width = 800
screen_height = int(screen_width * 0.8)
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Shooter")

# Set FPS
clock = pygame.time.Clock()
FPS = 60

# Game Variables
gravity = 0.75
scroll_threshold = 200
rows = 16
columns = 150
tile_size = screen_height // rows
tile_types = 21
max_levels = 3
screen_scroll = 0
bg_scroll = 0
level = 1
start_game = False
start_intro = False

# Player Action Variables
shoot = False
moving_left = False
moving_right = False
grenade = False
grenade_thrown = False
# moving_up = False
# moving_down = False

# load music and sounds
pygame.mixer.music.load('shooter_assets/audio/music2.mp3')
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1, 0.0, 5000)
jump_fx = pygame.mixer.Sound('shooter_assets/audio/jump.wav')
jump_fx.set_volume(0.5)
grenade_fx = pygame.mixer.Sound('shooter_assets/audio/grenade.wav')
grenade_fx.set_volume(0.5)
shot_fx = pygame.mixer.Sound('shooter_assets/audio/shot.wav')
shot_fx.set_volume(0.5)

# Load Images
# buttons
start_img = pygame.image.load('shooter_assets/img/start_btn.png').convert_alpha()
exit_img = pygame.image.load('shooter_assets/img/exit_btn.png').convert_alpha()
restart_img = pygame.image.load('shooter_assets/img/restart_btn.png').convert_alpha()

# background
pine_1_img = pygame.image.load('shooter_assets/img/background/pine1.png').convert_alpha()
pine_2_img = pygame.image.load('shooter_assets/img/background/pine2.png').convert_alpha()
mountain_img = pygame.image.load('shooter_assets/img/background/mountain.png').convert_alpha()
sky_img = pygame.image.load('shooter_assets/img/background/sky_cloud.png').convert_alpha()
# Store tiles in a list
img_list = []
for x in range(tile_types):
    img = pygame.image.load(f'shooter_assets/img/tile/{x}.png')
    img = pygame.transform.scale(img, (tile_size, tile_size))
    img_list.append(img)

# Bullet
bullet_img = pygame.image.load('shooter_assets/img/icons/bullet.png').convert_alpha()
# Grenade
grenade_img = pygame.image.load('shooter_assets/img/icons/grenade.png').convert_alpha()
# pick up boxes
health_box_img = pygame.image.load('shooter_assets/img/icons/health_box.png').convert_alpha()
ammo_box_img = pygame.image.load('shooter_assets/img/icons/ammo_box.png').convert_alpha()
grenade_box_img = pygame.image.load('shooter_assets/img/icons/grenade_box.png').convert_alpha()
item_boxes = {
    'Health' : health_box_img,
    'Ammo' : ammo_box_img,
    'Grenade' : grenade_box_img
}

# colors
BG = (144, 201, 120)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
BROWN = (106, 55, 5)

# fonts
font = pygame.font.SysFont('Futura', 30)

# function to reset level
def reset_level():
    enemy_group.empty()
    bullet_group.empty()
    grenade_group.empty()
    explosion_group.empty()
    item_box_group.empty()
    decoration_group.empty()
    water_group.empty()
    exit_group.empty()

    # create empty tile list
    data = []
    for row in range(rows):
        r = [-1] * columns
        data.append(r)

    return data

def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

def draw_bg():
    screen.fill(BG)
    # pygame.draw.line(screen, RED, (0, 300), (Screen_width, 300))
    width = sky_img.get_width()
    for x in range(5):
        screen.blit(sky_img, ((x * width) - bg_scroll * 0.5, 0))
        screen.blit(mountain_img, ((x * width) - bg_scroll * 0.6,screen_height - mountain_img.get_height() - 300))
        screen.blit(pine_1_img, ((x * width) - bg_scroll * 0.7, screen_height - pine_1_img.get_height() - 150))
        screen.blit(pine_2_img, ((x * width) - bg_scroll * 0.8, screen_height - pine_2_img.get_height()))


class Soldier(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed, ammo, grenades):
        # pygame.sprite.Sprite.__init__(self)
        super().__init__()
        self.alive = True
        self.char_type = char_type
        self.speed = speed
        self.ammo = ammo
        self.start_ammo = ammo
        self.shoot_cooldown = 0
        self.grenades = grenades
        self.health = 100
        self.max_health = self.health
        self.direction = 1
        self.vel_y = 0
        self.jump = False
        self.in_air = True
        self.flip = False
        self.animation_list = []
        self.frame_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()

        # create ai specific variables
        self.move_counter = 0
        self.vision = pygame.Rect(0, 0, 150, 20)
        self.idling = False
        self.idling_counter = 0
        
        # Load all images for the players
        animation_types = ['Idle', 'Run', 'Jump', 'Death']
        for animation in animation_types:
            # Reset temporary list of images
            temp_list = []
            # Count number of files in the folder
            num_of_frames = len(os.listdir(f'shooter_assets/img/{self.char_type}/{animation}'))
            
            for i in range(num_of_frames):
                img = pygame.image.load(f'shooter_assets/img/{self.char_type}/{animation}/{i}.png').convert_alpha()
                img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
                temp_list.append(img)
            self.animation_list.append(temp_list)

            
        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def update(self):
        self.update_animation()
        self.check_alive()
        # Update cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def move(self, moving_left, moving_right):
        screen_scroll = 0
        # Reset movement variables
        dx = 0
        dy = 0

        # Assign movement variables based on key presses
        if moving_left:
            dx = -self.speed
            self.flip = True
            self.direction = -1
        if moving_right:
            dx = self.speed
            self.flip = False
            self.direction = 1

        # Jump
        if self.jump == True and self.in_air == False:
            self.vel_y = -11
            self.jump = False
            self.in_air = True

        dy += self.vel_y
        
        self.vel_y += gravity

        # Check for collision
        for tile in world.obstacle_list:
            # Check collision in x direction
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                dx = 0
                # If the ai has hit a wall then make it turn around
                if self.char_type == 'enemy':
                    self.direction *= -1
            # Check collision in y direction
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                # Check if below the ground, i.e. jumping
                if self.vel_y < 0:
                    dy = tile[1].bottom - self.rect.top
                    self.vel_y = 0
                # Check if above the ground, i.e. falling
                elif self.vel_y >= 0:
                    dy = tile[1].top - self.rect.bottom
                    self.vel_y = 0
                    self.in_air = False

        # Check for collision with water
        if pygame.sprite.spritecollide(self, water_group, False):
            self.health = 0

        # Check for collision with exit
        level_complete = False
        if pygame.sprite.spritecollide(self, exit_group, False):
            level_complete = True

        # Check if falling off the map
        if self.rect.bottom > screen_height:
            self.health = 0
        
        # Check if player going off screen
        if self.char_type == 'player':
            if self.rect.left + dx < 0 or self.rect.right + dx > screen_width:
                dx = 0

        # Update rectangle position
        self.rect.x += dx
        self.rect.y += dy

        # Update scroll based on player position
        if self.char_type == 'player':
           if (self.rect.right > screen_width - scroll_threshold and bg_scroll < (world.level_length * tile_size) - screen_width) or (self.rect.left < scroll_threshold and bg_scroll > abs(dx)):
               self.rect.x -= dx
               screen_scroll = -dx

        return screen_scroll, level_complete

    def shoot(self):
        if self.shoot_cooldown == 0 and self.ammo > 0:
           self.shoot_cooldown = 20
           bullet = Bullet(self.rect.centerx + (0.75 * self.rect.size[0] * self.direction), self.rect.centery, self.direction)
           bullet_group.add(bullet)
           
           # Reduce ammo
           self.ammo -= 1
           shot_fx.play()

    def ai(self):
        if self.alive and player.alive:
            if  self.idling == False and random.randint(1, 200) == 1:
                self.update_action(0) # 0: idle
                self.idling = True
                self.idling_counter = 50

            # Check if the ai in near the player
            if self.vision.colliderect(player.rect):
                # Stop running and face the player
                self.update_action(0) # 0: idle
                # Shoot
                self.shoot()
            else:
                    
                if self.idling == False:
                    if self.direction == 1:
                        ai_moving_right = True
                    else:
                        ai_moving_right = False
                    ai_moving_left = not ai_moving_right
                    self.move(ai_moving_left, ai_moving_right)
                    self.update_action(1) # 1: run
                    self.move_counter += 1
                    
                    # Update ai vision as the enemy moves
                    self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)

                    if self.move_counter > tile_size:
                        self.direction *= -1
                        self.move_counter *= -1

                else:
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False
        
        self.rect.x += screen_scroll

    def update_animation(self):
        # Update animation
        animation_cooldown = 100

        # Update image depending on current frame
        self.image = self.animation_list[self.action][self.frame_index]

        # Check if enough time has passed since the last update
        if pygame.time.get_ticks() - self.update_time > animation_cooldown:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1 

        # If the animation has run out, reset back to the start
        if self.frame_index >= len(self.animation_list[self.action]):
            # If the player is dead, end the animation there
            if self.action == 3:
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
                self.frame_index = 0

    def update_action(self, new_action):
        # Check if the new action is different to the previous one
        if new_action != self.action:
            self.action = new_action
            # Update the animation settings
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def check_alive(self):
        if self.health <= 0:
            self.health = 0
            self.speed = 0
            self.alive = False
            self.update_action(3)

    def draw(self):
        screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)

class World():
    def __init__(self):
        self.obstacle_list = []

    def process_data(self, data):
        self.level_length = len(data[0])
        # Iterate through each value in level data file
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    img = img_list[tile]
                    img_rect = img.get_rect()
                    img_rect.x = x * tile_size
                    img_rect.y = y * tile_size
                    tile_data = (img, img_rect)
                    if tile >= 0 and tile <= 8:
                        self.obstacle_list.append(tile_data)
                    elif tile >= 9 and tile <= 10:
                        pass
                        water = Water(img, x * tile_size, y * tile_size)
                        water_group.add(water)
                    elif tile >= 11 and tile <= 14:
                        decoration = Decoration(img, x * tile_size, y * tile_size)
                        decoration_group.add(decoration) 
                    elif tile == 15: # create player
                        player = Soldier("player", x * tile_size, y * tile_size, 1.65, 5, 20, 5)
                        health_bar = HealthBar(10, 10, player.health, player.max_health)
                    elif tile == 16: # create enemies
                        # print("enemy spawned at: ", x, y)
                        enemy = Soldier("enemy", x * tile_size, y * tile_size, 1.65, 3, 20, 0)
                        enemy_group.add(enemy)
                        
                    elif tile == 17: # create ammo box
                        item_box = ItemBox('Ammo', x * tile_size, y * tile_size)
                        item_box_group.add(item_box)
                    elif tile == 18: # create grenade box
                        item_box = ItemBox('Grenade', x * tile_size, y * tile_size)
                        item_box_group.add(item_box)
                    elif tile == 19: # create health box
                        item_box = ItemBox('Health', x * tile_size, y * tile_size)
                        item_box_group.add(item_box)
                    elif tile == 20: # exit
                        exit = Exit(img, x * tile_size, y * tile_size)
                        exit_group.add(exit)
                   
        return player, health_bar
    
    def draw(self):
        for tile in self.obstacle_list:
            tile[1][0] += screen_scroll
            screen.blit(tile[0], tile[1])

class Decoration(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        super().__init__()
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + tile_size // 2, y + (tile_size - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll

class Water(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        super().__init__()
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + tile_size // 2, y + (tile_size - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll

class Exit(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        super().__init__()
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + tile_size // 2, y + (tile_size - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll

class ItemBox(pygame.sprite.Sprite):
    def __init__(self, item_type, x, y):
        super().__init__()
        self.item_type = item_type
        self.image = item_boxes[self.item_type]
        self.rect = self.image.get_rect()
        # self.rect.midtop = (x * tile_size // 2, y + (tile_size - self.image.get_height()))
        self.rect.midtop = (x, y)

    def update(self):
        # Scroll the item box with the world
        self.rect.x += screen_scroll
        # Check if the player has picked up the item
        if pygame.sprite.collide_rect(self, player):
            # Check what type of item it was
            if self.item_type == 'Health':
                player.health += 25
                if player.health > player.max_health:
                    player.health = player.max_health
            elif self.item_type == 'Ammo':
                player.ammo += 15
            elif self.item_type == 'Grenade':
                player.grenades += 3
            # Delete the item
            self.kill()

class HealthBar():
    def __init__(self, x, y, health, max_health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health

    def draw(self, health):
        # Update health bar width
        self.health = health
        # Calculate health ratio
        ratio = self.health / self.max_health
        pygame.draw.rect(screen, BLACK, (self.x - 2, self.y - 2, 154, 24))
        pygame.draw.rect(screen, RED, (self.x, self.y, 150, 20))
        pygame.draw.rect(screen, GREEN, (self.x, self.y, 150 * ratio, 20))

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__()
        self.speed = 10
        self.image = pygame.transform.scale(bullet_img, (20, 10))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction

    def update(self):
        # Move bullet
        self.rect.x += (self.direction * self.speed) + screen_scroll
        # Check if bullet has gone off screen
        if self.rect.right < 0 or self.rect.left > screen_width - 100:
            self.kill()

        # Check for collision with levels
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                self.kill()

        # Check for collisions with characters
        if pygame.sprite.spritecollide(player, bullet_group, False):
            if player.alive:
                player.health -= 5
                self.kill()
        for enemy in enemy_group: 
            if pygame.sprite.spritecollide(enemy, bullet_group, False):
                if enemy.alive:
                    enemy.health -= 25
                    self.kill()

class Grenade(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__()
        self.timer = 100
        self.vel_y = -11
        self.speed = 7
        self.image = grenade_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.direction = direction

    def update(self):
        self.vel_y += gravity
        dx = self.direction * self.speed
        dy = self.vel_y

        # Check for collision with levels
        for tile in world.obstacle_list:
            # Check collision in x direction
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                self.direction *= -1
                dx = self.direction * self.speed
            # Check collision in y direction
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                self.speed = 0
                # Check if below the ground, i.e. thrown up
                if self.vel_y < 0:
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top
                # Check if above the ground, i.e. thrown down
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    dy = tile[1].top - self.rect.bottom

        # # Check for collision with floor
        # if self.rect.bottom + dy > 300:
        #     dy = 300 - self.rect.bottom
        #     self.speed = 0

        # # Check for collision with walls
        # if self.rect.left + dx < 0 or self.rect.right + dx > Screen_width - 100:
        #     self.direction *= -1
        #     dx = self.direction * self.speed
            
        # update grenade position
        self.rect.x += dx + screen_scroll
        self.rect.y += dy

        # countdown timer
        self.timer -= 1
        if self.timer <= 0:
            self.kill()
            grenade_fx.play()
            explosion = Explosion(self.rect.x, self.rect.y, 2)
            explosion_group.add(explosion)

            # Do damage to anyone that is nearby 
            if abs(self.rect.centerx - player.rect.centerx) < tile_size * 2  and abs(self.rect.centery - player.rect.centery) < tile_size * 2:
                player.health -= 50
            for enemy in enemy_group:
                if abs(self.rect.centerx - enemy.rect.centerx) < tile_size * 2  and abs(self.rect.centery - enemy.rect.centery) < tile_size * 2:
                    enemy.health -= 50

class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, scale):
        super().__init__()
        self.images = []
        for num in range(1, 6):
            img = pygame.image.load(f'shooter_assets/img/Explosion/exp{num}.png').convert_alpha()
            img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
            self.images.append(img)
        self.frame_index = 0 
        self.image = self.images[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.counter = 0 

    def update(self):
        # scroll the explosion
        self.rect.x += screen_scroll
        explosion_speed = 4
        # update explosion animation
        self.counter += 1

        if self.counter >= explosion_speed:
            self.counter = 0
            self.frame_index += 1
            # If the animation is complete then delete the explosion
            if self.frame_index >= len(self.images):
                self.kill()
            else:
                self.image = self.images[self.frame_index]

class ScreenFade():
    def __init__(self, direction, colour, speed):
        self.direction = direction
        self.colour = colour
        self.speed = speed
        self.fade_counter = 0

    def fade(self):
        fade_complete = False
        self.fade_counter += self.speed

        if self.direction == 1: # Whole screen fade
            pygame.draw.rect(screen, self.colour, (0 - self.fade_counter, 0, screen_width // 2, screen_height))
            pygame.draw.rect(screen, self.colour, (screen_width // 2 + self.fade_counter, 0, screen_width // 2, screen_height))
            pygame.draw.rect(screen, self.colour, (0, 0 - self.fade_counter, screen_width, screen_height // 2))
            pygame.draw.rect(screen, self.colour, (0, screen_height // 2 + self.fade_counter, screen_width, screen_height // 2))

        if self.direction == 2: # Vertical fade to black
            pygame.draw.rect(screen, self.colour, (0, 0, screen_width, 0 + self.fade_counter))

        if self.fade_counter >= screen_height:
            fade_complete = True

        return fade_complete

# Create screen fades
intro_fade = ScreenFade(1, BLACK, 4)
death_fade = ScreenFade(2, RED, 4)

# Create buttons
start_button = button.Button(screen_width // 2 - 130, screen_height // 2 - 150, start_img, 1)
exit_button = button.Button(screen_width // 2 - 110, screen_height // 2 + 50, exit_img, 1)
restart_button = button.Button(screen_width // 2 - 100, screen_height // 2 - 50, restart_img, 2)

# Create sprite groups
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
water_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

# create empty tile list
world_data = []
for row in range(rows):
    r = [-1] * columns
    world_data.append(r)

# load in level data and create world
with open(f'shooter_assets/level{level}_data.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for x, row in enumerate(reader):
        for y, tile in enumerate(row):
            world_data[x][y] = int(tile)
world = World()
player, health_bar = world.process_data(world_data)

# Main Game Loop
run = True
while run:
    clock.tick(FPS)

    if start_game == False:
        # draw menu
        screen.fill(BG)
        # add buttons
        if start_button.draw(screen):
            start_game = True
            start_intro = True
        if exit_button.draw(screen):
            run = False

    else:
        # draw background
        draw_bg()
        # draw world map
        world.draw()
        # Draw and update health bars
        health_bar.draw(player.health)
        # show ammo
        draw_text('AMMO:', font, WHITE, 10, 35)
        for x in range(player.ammo):
            screen.blit(bullet_img, (90 + (x * 10), 40))

        # show grenades
        draw_text('GRENADES:', font, WHITE, 10, 60)
        for x in range(player.grenades):
            screen.blit(grenade_img, (135 + (x * 15), 60))

        player.update()
        player.draw()

        for enemy in enemy_group:
            enemy.ai()
            enemy.update()
            enemy.draw()

        # Update and draw groups
        bullet_group.update()
        grenade_group.update()
        explosion_group.update()
        item_box_group.update()
        decoration_group.update()
        water_group.update()
        exit_group.update()

        bullet_group.draw(screen)
        grenade_group.draw(screen)
        explosion_group.draw(screen)
        item_box_group.draw(screen)
        decoration_group.draw(screen)
        water_group.draw(screen)
        exit_group.draw(screen)

        # Show intro
        if start_intro == True:
            if intro_fade.fade():
                start_intro = False
                intro_fade.fade_counter = 0

        if player.alive:
            # Shoot bullets
            if shoot:
                player.shoot()
            
            # Throw grenades
            elif grenade and grenade_thrown == False and player.grenades > 0:
                grenade = Grenade(player.rect.centerx + (0.5 * player.rect.size[0] * player.direction), \
                            player.rect.top, player.direction)
                grenade_group.add(grenade)
                # Reduce grenades
                player.grenades -= 1
                grenade_thrown = True
            # Update player actions
            if player.in_air:
                player.update_action(2)  # 2: Jump
            elif moving_left or moving_right:
                player.update_action(1)  # 1: Run
            else:
                player.update_action(0)  # 0: Idle
            screen_scroll, level_complete = player.move(moving_left, moving_right)
            bg_scroll -= screen_scroll
            # check if player has completed the level
            if level_complete:
                start_intro = True
                level += 1
                bg_scroll = 0
                world_data = reset_level()
                if level <= max_levels:
                # load in level data and create world
                    with open(f'shooter_assets/level{level}_data.csv', newline='') as csvfile:
                        reader = csv.reader(csvfile, delimiter=',')
                        for x, row in enumerate(reader):
                            for y, tile in enumerate(row):
                                world_data[x][y] = int(tile)   
                    world = World()
                    player, health_bar = world.process_data(world_data)

        else:
            screen_scroll = 0
            if death_fade.fade():
                if restart_button.draw(screen):
                    death_fade.fade_counter = 0
                    start_intro = True
                    bg_scroll = 0
                    world_data = reset_level()
                    # load in level data and create world
                    with open(f'shooter_assets/level{level}_data.csv', newline='') as csvfile:
                        reader = csv.reader(csvfile, delimiter=',')
                        for x, row in enumerate(reader):
                            for y, tile in enumerate(row):
                                world_data[x][y] = int(tile)
                    
                    world = World()
                    player, health_bar = world.process_data(world_data)
                    
                    start_game = False

    for event in pygame.event.get():
        # Check for QUIT event
        if event.type == pygame.QUIT:
            run = False
        
        # KeyBoard presses
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                moving_left = True
            if event.key == pygame.K_RIGHT:
                moving_right = True
            if event.key == pygame.K_s:
                shoot = True
            if event.key == pygame.K_x:
                grenade = True
            # jump with up arrow or space and player should be alive
            if event.key == pygame.K_UP or event.key == pygame.K_SPACE:
                player.jump = True
                jump_fx.play()       
            if event.key == pygame.K_ESCAPE:
                run = False
        
        # KeyBoard releases
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a or event.key == pygame.K_LEFT:
                moving_left = False
            if event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                moving_right = False
            if event.key == pygame.K_s:
                shoot = False
            if event.key == pygame.K_x:
                grenade = False
                grenade_thrown = False
            if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                player.jump = False 
            # if event.key == pygame.K_w or event.key == pygame.K_UP:
            #     moving_up = False
            # if event.key == pygame.K_s or event.key == pygame.K_DOWN:
            #     moving_down = False


    pygame.display.update()

pygame.quit()