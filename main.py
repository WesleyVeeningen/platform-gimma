import pygame
import os
from platforms import (
    generate_initial_platforms,
    extend_platforms_if_needed,
    draw_platforms
)
from settings import (
    platform_min_gap, platform_max_gap,
    platform_min_width, platform_max_width,
    platform_base_y, platform_double_chance,
    player_width, player_height
)
from player import Player

# --- Pygame setup ---
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("2D Platformer")
clock = pygame.time.Clock()

# --- Load and scale background (optional) ---
background = None
bg_path = os.path.join('images', 'background.jpeg')
if os.path.exists(bg_path):
    try:
        background = pygame.image.load(bg_path)
        background = pygame.transform.scale(background, (800, 600))
    except Exception:
        background = None

# --- Camera ---
camera_scroll_x = 0

# --- Create starting platforms ---
platforms = generate_initial_platforms(
    amount_of_platforms=10,
    min_gap=platform_min_gap,
    max_gap=platform_max_gap,
    min_width=platform_min_width,
    max_width=platform_max_width,
    base_y=platform_base_y,
    double_chance=platform_double_chance
)

# --- Create guaranteed left ground platform so player never starts falling ---
ground_height = 40
ground_width = max(screen.get_width() * 2, platform_min_width)
left_ground = pygame.Rect(0, platform_base_y, int(ground_width), ground_height)

# Ensure left_ground is first and does not overlap incorrectly with existing first
if not platforms or platforms[0].x != 0:
    platforms.insert(0, left_ground)
else:
    # make sure the existing first platform starts at 0 and is wide enough
    platforms[0].x = 0
    if platforms[0].width < player_width + 20:
        platforms[0].width = player_width + 20

# --- Create player and group ---
player = Player()

first_plat = platforms[0]

# place player slightly inside the first platform and on top of it
player.x = first_plat.x + 10
player.y = first_plat.y - player_height
player.vel_y = 0
player.on_ground = True

# ensure sprite rect matches world coordinates (camera initially 0)
camera_scroll_x = 0
player.rect.topleft = (int(player.x - camera_scroll_x), int(player.y))

player_group = pygame.sprite.Group()
player_group.add(player)

# debug toggle
DEBUG = True

# --- Main game loop ---
running = True
start_safe_frames = 30   # skip game-over check for the first N frames
frame_count = 0

while running:
    dt = clock.tick(60)
    frame_count += 1

    # --- Event handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- Camera movement: follow player ---
    camera_scroll_x = max(0, int(player.x - screen.get_width() * 0.25))

    # --- Extend platforms as camera moves ---
    extend_platforms_if_needed(
        platforms,
        camera_scroll_x,
        screen.get_width(),
        platform_min_gap,
        platform_max_gap,
        platform_min_width,
        platform_max_width,
        platform_base_y,
        platform_double_chance
    )

    # --- Update player (pass platforms and camera offset) ---
    player_group.update(platforms, camera_scroll_x)

    # --- Debug output ---
    if DEBUG:
        print(
            f"frame={frame_count} player.world=({player.x:.1f},{player.y:.1f}) "
            f"vel_y={getattr(player,'vel_y',0):.2f} on_ground={getattr(player,'on_ground',False)} "
            f"rect={player.rect} camera={camera_scroll_x}"
        )
        for i, plat in enumerate(platforms[:6]):
            print(f"  plat[{i}] = x={plat.x} y={plat.y} w={plat.width} h={plat.height}")

    # --- End game if player goes off-screen (but give a short grace at start) ---
    screen_rect = pygame.Rect(0, 0, screen.get_width(), screen.get_height())
    if frame_count > start_safe_frames and not player.rect.colliderect(screen_rect):
        print("Player left the screen — exiting.")
        running = False

    # --- Draw everything ---
    screen.fill((30, 30, 30))
    if background:
        screen.blit(background, (0, 0))
    draw_platforms(screen, camera_scroll_x, platforms)
    player_group.draw(screen)

    pygame.display.flip()

pygame.quit()