# Infinite platformer with full camera following

import pygame
import sys
import random

# --- Window settings ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# --- Colors ---
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

# --- Player settings ---
PLAYER_WIDTH = 50
PLAYER_HEIGHT = 50
PLAYER_COLOR = BLUE
PLAYER_SPEED = 5
GRAVITY = 0.5
JUMP_STRENGTH = 12

# --- Platform settings ---
PLATFORM_WIDTH_MIN = 100
PLATFORM_WIDTH_MAX = 300
PLATFORM_HEIGHT = 20
PLATFORM_GAP_MIN = 100
PLATFORM_GAP_MAX = 250

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Infinite Platformer")
clock = pygame.time.Clock()

# --- Player class ---
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT))
        self.image.fill(PLAYER_COLOR)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False

    def update(self, platforms):
        keys = pygame.key.get_pressed()
        self.vel_x = 0
        if keys[pygame.K_LEFT]:
            self.vel_x = -PLAYER_SPEED
        if keys[pygame.K_RIGHT]:
            self.vel_x = PLAYER_SPEED

        self.rect.x += self.vel_x

        # Gravity
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y

        # Check collisions with platforms
        self.on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform.rect) and self.vel_y >= 0:
                self.rect.bottom = platform.rect.top
                self.vel_y = 0
                self.on_ground = True

    def jump(self):
        if self.on_ground:
            self.vel_y = -JUMP_STRENGTH

# --- Platform class ---
class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width):
        super().__init__()
        self.image = pygame.Surface((width, PLATFORM_HEIGHT))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect(topleft=(x, y))

# --- Sprite groups ---
player = Player(0, 0)
player_group = pygame.sprite.Group(player)
platforms = pygame.sprite.Group()

# --- Camera offset ---
camera_x = 0
camera_y = 0

# --- Infinite world generator ---
world_width = 0
world_height = 0

def generate_platform():
    global world_width, world_height
    width = random.randint(PLATFORM_WIDTH_MIN, PLATFORM_WIDTH_MAX)
    gap_x = random.randint(PLATFORM_GAP_MIN, PLATFORM_GAP_MAX)
    gap_y = random.randint(-150, 200)  # vertical randomness
    x = world_width + gap_x
    y = world_height + gap_y
    if y > SCREEN_HEIGHT - 50:
        y = SCREEN_HEIGHT - 50
    elif y < 0:
        y = 0
    platforms.add(Platform(x, y, width))
    world_width = x + width
    world_height = y

# Generate initial platforms
platforms.add(Platform(-200, SCREEN_HEIGHT - 50, SCREEN_WIDTH + 400))
for _ in range(20):
    generate_platform()

# --- Main game loop ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                player.jump()

    # Update
    player.update(platforms)

    # Camera follows player
    camera_x = player.rect.centerx - SCREEN_WIDTH // 2
    camera_y = player.rect.centery - SCREEN_HEIGHT // 2

    # Generate new platforms ahead
    while world_width - camera_x < SCREEN_WIDTH + 200:
        generate_platform()

    # Draw
    screen.fill(WHITE)
    for platform in platforms:
        screen.blit(platform.image, (platform.rect.x - camera_x, platform.rect.y - camera_y))

    player_group.draw(screen)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()