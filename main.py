import time
import pygame
import os
import random
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

import blackjack  # to ensure blackjack.py is included in the package
from blackjack import load_card_images, load_card_back_image

# --- Pygame setup ---
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("2D Platformer")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 28)

# --- Load and scale background (optional) ---
background = None
bg_path = os.path.join('images', 'background.jpeg')
if os.path.exists(bg_path):
    try:
        background = pygame.image.load(bg_path)
        background = pygame.transform.scale(background, (800, 600))
    except Exception:
        background = None

# --- Load coin image (fish) ---
fish_path = os.path.join('images', 'fish.png')
if os.path.exists(fish_path):
    fish_img = pygame.image.load(fish_path).convert_alpha()
    COIN_W, COIN_H = 32, 32
    fish_img = pygame.transform.scale(fish_img, (COIN_W, COIN_H))
else:
    # fallback colored circle surface
    COIN_W, COIN_H = 24, 24
    fish_img = pygame.Surface((COIN_W, COIN_H), pygame.SRCALPHA)
    pygame.draw.circle(fish_img, (255, 200, 0),
                       (COIN_W//2, COIN_H//2), COIN_W//2)

# --- Load orca image (enemy) ---
orca_path = os.path.join('images', 'orca.png')
if os.path.exists(orca_path):
    orca_img = pygame.image.load(orca_path).convert_alpha()
    ORCA_W, ORCA_H = 64, 48
    orca_img = pygame.transform.scale(orca_img, (ORCA_W, ORCA_H))
else:
    ORCA_W, ORCA_H = 48, 32
    orca_img = pygame.Surface((ORCA_W, ORCA_H), pygame.SRCALPHA)
    pygame.draw.rect(orca_img, (0, 120, 180), (0, 0, ORCA_W, ORCA_H))

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

# --- Coins: store as world-space rects ---
coins = []  # list of pygame.Rect in world coordinates
orcas = []  # list of pygame.Rect for enemies (world coords)
score = 0
distance = 0  # number of platforms passed
platforms_passed_threshold = 0  # track the X position to detect platform passes
distance_tracking_enabled = True  # flag to enable/disable distance tracking

# spawn tuning: make coins rarer and only attempt once per platform
INITIAL_COIN_CHANCE = 0.40     # chance when creating initial platforms
NEW_PLATFORM_COIN_CHANCE = 0.40  # chance for newly extended platforms

# Orca spawn rates (reduced)
INITIAL_ORCA_CHANCE = 0.1     # lower chance for initial orca spawn on platforms
NEW_ORCA_CHANCE = 0.1         # lower chance for newly-seen platforms

# track platforms we've already attempted to spawn a coin/orca for
checked_platforms = set()


def spawn_coin_on_platform(plat):
    # place coin centered on platform, just above it
    cx = plat.x + plat.width // 2 - COIN_W // 2
    cy = plat.y - COIN_H - 8
    if cy < 0:
        cy = max(0, plat.y - COIN_H - 4)
    coin_rect = pygame.Rect(cx, cy, COIN_W, COIN_H)
    coins.append(coin_rect)


def spawn_orca_on_platform(plat):
    # place orca centered on platform, standing on top of it
    ox = plat.x + plat.width // 2 - ORCA_W // 2
    oy = plat.y - ORCA_H + 2  # small overlap so it looks like it sits on the platform
    orca_rect = pygame.Rect(ox, oy, ORCA_W, ORCA_H)
    orcas.append(orca_rect)


# spawn initial coins for platforms (skip the guaranteed left ground to avoid too many)
for i, plat in enumerate(platforms):
    # mark this platform as checked so we only try once
    checked_platforms.add(id(plat))
    if i == 0:
        # small chance on the left ground; normally skip
        if random.random() < (INITIAL_COIN_CHANCE * 0.5):
            spawn_coin_on_platform(plat)
        continue
    if random.random() < INITIAL_COIN_CHANCE:
        spawn_coin_on_platform(plat)
    # rare initial orca spawns (skip left ground if present)
    if random.random() < INITIAL_ORCA_CHANCE:
        spawn_orca_on_platform(plat)

# --- Create player and group ---
player = Player()
player_group = pygame.sprite.Group()
player_group.add(player)

# --- Game state flags ---
game_over = False

# Restart button visuals
RESTART_W, RESTART_H = 220, 56
restart_btn_rect = pygame.Rect((screen.get_width()//2 - RESTART_W//2,
                                screen.get_height()//2 + 30,
                                RESTART_W, RESTART_H))


def play_blackjack_minigame(screen, font, pygame):
    """
    Simple blackjack minigame. Player draws cards trying to get 21 or beat dealer.
    Returns True if player wins, False if player loses or busts.
    """
    cards = blackjack.Cards()

    # Deal initial hands
    player_hand = [cards.deal_card(), cards.deal_card()]
    dealer_hand = [cards.deal_card(), cards.deal_card()]

    player_value = cards.calculate_hand_value(player_hand)
    dealer_value = cards.calculate_hand_value(dealer_hand)

    player_turn = True
    game_complete = False
    player_won = False
    player_stood = False  # Track when player stands to reveal dealer's second card
    dealer_playing = False  # Track when dealer is drawing cards
    dealer_finished = False  # Track when dealer is done drawing
    last_card_time = 0  # Track time for dealer card draws

    # Load card back image for hidden cards
    card_back_img = load_card_back_image()

    minigame_clock = pygame.time.Clock()

    # Minigame loop
    while not game_complete:
        dt = minigame_clock.tick(60)
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if player_turn:
                    if event.key == pygame.K_h:  # Hit
                        player_hand.append(cards.deal_card())
                        player_value = cards.calculate_hand_value(player_hand)
                        if player_value > 21:
                            player_turn = False
                            game_complete = True
                    elif event.key == pygame.K_s:  # Stand
                        player_turn = False
                        player_stood = True
                        dealer_playing = True
                        last_card_time = current_time

        # Dealer plays - draw one card per second
        if dealer_playing and not dealer_finished:
            current_dealer_value = cards.calculate_hand_value(dealer_hand)
            if current_dealer_value < 17 and current_time - last_card_time >= 1000:
                dealer_hand.append(cards.deal_card())
                last_card_time = current_time
            elif current_dealer_value >= 17:
                dealer_finished = True
                dealer_value = cards.calculate_hand_value(dealer_hand)
                game_complete = True

        # Draw minigame
        screen.fill((30, 70, 30))

        # Title
        title = font.render(
            "BLACKJACK - Press H to Hit, S to Stand", True, (255, 255, 255))
        screen.blit(title, (10, 10))

        # Dealer hand with card images
        dealer_label = font.render("Dealer:", True, (200, 50, 50))
        screen.blit(dealer_label, (10, 70))

        dealer_images = load_card_images(dealer_hand)
        card_x = 10
        for i, card_img in enumerate(dealer_images):
            if i == 1 and not player_stood:
                # Hide second card until player stands
                screen.blit(card_back_img, (card_x, 100))
            else:
                screen.blit(card_img, (card_x, 100))
            card_x += 95

        # Show dealer value only when standing or complete
        if player_stood or game_complete:
            dealer_value_text = font.render(
                f"Value: {cards.calculate_hand_value(dealer_hand)}", True, (200, 50, 50))
            screen.blit(dealer_value_text, (10, 235))

        # Player hand with card images
        player_label = font.render("Player:", True, (50, 200, 50))
        screen.blit(player_label, (10, 270))

        player_images = load_card_images(player_hand)
        card_x = 10
        for card_img in player_images:
            screen.blit(card_img, (card_x, 290))
            card_x += 95

        # Player value always shown
        player_value = cards.calculate_hand_value(player_hand)
        player_value_text = font.render(
            f"Value: {player_value}", True, (50, 200, 50))
        screen.blit(player_value_text, (10, 425))

        # Status
        if player_value > 21:
            status = font.render("BUST! You lose.", True, (255, 50, 50))
            screen.blit(status, (10, 450))
            player_won = False
        elif game_complete:
            dealer_value = cards.calculate_hand_value(dealer_hand)
            if dealer_value > 21:
                status = font.render(
                    "Dealer BUST! You win!", True, (50, 255, 50))
                player_won = True
            elif player_value > dealer_value:
                status = font.render("You win!", True, (50, 255, 50))
                player_won = True
            elif player_value < dealer_value:
                status = font.render(
                    "Dealer wins. You lose.", True, (255, 50, 50))
                player_won = False
            else:
                status = font.render(
                    "Push (tie). You lose.", True, (255, 200, 50))
                player_won = False
            screen.blit(status, (10, 450))
        elif player_turn:
            status = font.render(
                "Your turn! Press H to Hit, S to Stand", True, (200, 200, 50))
            screen.blit(status, (10, 450))

        time.sleep(1)  # add delay on closing the window to see result
        pygame.display.flip()

    return player_won


def reset_game():
    """
    Reset all mutable game state to start a fresh run.
    Uses globals because main.py manages top-level state.
    """
    global platforms, left_ground, coins, orcas, checked_platforms, score
    global camera_scroll_x, frame_count, game_over, player, player_group
    global distance, platforms_passed_threshold, distance_tracking_enabled

    # recreate platforms and guaranteed left ground
    platforms = generate_initial_platforms(
        amount_of_platforms=10,
        min_gap=platform_min_gap,
        max_gap=platform_max_gap,
        min_width=platform_min_width,
        max_width=platform_max_width,
        base_y=platform_base_y,
        double_chance=platform_double_chance
    )

    ground_height = 40
    ground_width = max(screen.get_width() * 2, platform_min_width)
    left_ground = pygame.Rect(
        0, platform_base_y, int(ground_width), ground_height)
    if not platforms or platforms[0].x != 0:
        platforms.insert(0, left_ground)
    else:
        platforms[0].x = 0
        if platforms[0].width < player_width + 20:
            platforms[0].width = player_width + 20

    # clear enemies/coins and tracking set
    coins = []
    orcas = []
    checked_platforms = set()

    # reset score and camera
    score = 0
    distance = 0
    platforms_passed_threshold = 0
    distance_tracking_enabled = True
    camera_scroll_x = 0
    frame_count = 0

    # reset player to starting platform
    player.x = platforms[0].x + 10
    player.y = platforms[0].y - player_height
    player.vel_y = 0
    player.on_ground = True
    player.jumps_left = player.max_jumps
    player.rect.topleft = (int(player.x - camera_scroll_x), int(player.y))

    # mark initial platforms as checked and possibly spawn a few things (rare)
    for i, plat in enumerate(platforms):
        checked_platforms.add(id(plat))
        if i == 0:
            if random.random() < (INITIAL_COIN_CHANCE * 0.5):
                spawn_coin_on_platform(plat)
            continue
        if random.random() < INITIAL_COIN_CHANCE:
            spawn_coin_on_platform(plat)
        if random.random() < INITIAL_ORCA_CHANCE:
            spawn_orca_on_platform(plat)

    game_over = False


# ensure initial state uses reset_game() semantics
reset_game()

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

        # If game over, check for restart click
        if game_over and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if restart_btn_rect.collidepoint(event.pos):
                reset_game()

    # if game is over, skip updates but still draw and accept clicks
    if not game_over:
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

        # spawn coins/orcas on newly created platforms (attempt once per platform)
        for plat in platforms:
            pid = id(plat)
            if pid in checked_platforms:
                continue
            checked_platforms.add(pid)
            if plat is left_ground and random.random() > 0.10:
                continue
            if random.random() < NEW_PLATFORM_COIN_CHANCE:
                spawn_coin_on_platform(plat)
            if random.random() < NEW_ORCA_CHANCE:
                spawn_orca_on_platform(plat)

        # --- Update player (pass platforms and camera offset) ---
        player_group.update(platforms, camera_scroll_x)

        # --- Track distance (platforms passed) ---
        if distance_tracking_enabled:
            for plat in platforms:
                # Count each platform as passed once when player moves past its right edge
                if plat is not left_ground:  # Don't count the starting ground
                    if plat.right <= platforms_passed_threshold and plat.x > 0:
                        continue  # Already counted
                    if player.x > plat.right and plat.right > platforms_passed_threshold:
                        distance += 1
                        platforms_passed_threshold = plat.right

        # --- Coin collection: use player's world rect and remove immediately ---
        player_world_rect = pygame.Rect(int(player.x), int(
            player.y), player_width, player_height)
        for coin in coins[:]:
            if player_world_rect.colliderect(coin):
                score += 1
                coins.remove(coin)

        # --- Orca collision: touching an orca ends the run (enter game_over state) ---
        for orca in orcas:
            if player_world_rect.colliderect(orca):
                game_over = True
                # Check if player has 5+ coins for a chance to continue
                if score >= 5:
                    score -= 5  # Cost 5 coins to play
                    if play_blackjack_minigame(screen, font, pygame):
                        # Player won! Continue the game
                        game_over = False
                        # Reset threshold to continue tracking
                        platforms_passed_threshold = int(player.x)
                break

    # --- Debug output ---
    if DEBUG:
        pass

    # --- End game if player goes off-screen (but give a short grace at start) ---
    screen_rect = pygame.Rect(0, 0, screen.get_width(), screen.get_height())
    if not game_over and frame_count > start_safe_frames and not player.rect.colliderect(screen_rect):
        game_over = True
        # Check if player has 5+ coins for a chance to continue
        if score >= 5:
            score -= 5  # Cost 5 coins to play
            if play_blackjack_minigame(screen, font, pygame):
                # Player won! Continue the game
                game_over = False
                # Reset player position to a safe spot
                player.x = platforms[0].x + 10
                player.y = platforms[0].y - player_height
                player.vel_y = 0
                player.on_ground = True
                player.jumps_left = player.max_jumps
                # Reset threshold to continue tracking
                platforms_passed_threshold = int(player.x)

    # --- Draw everything ---
    screen.fill((30, 30, 30))
    if background:
        screen.blit(background, (0, 0))

    # draw platforms, coins, and orcas
    draw_platforms(screen, camera_scroll_x, platforms)
    for coin in coins:
        screen.blit(fish_img, (coin.x - camera_scroll_x, coin.y))
    for orca in orcas:
        screen.blit(orca_img, (orca.x - camera_scroll_x, orca.y))

    player_group.draw(screen)

    # draw coin counter and distance counter top-right
    txt = font.render(f"Coins: {score}", True, (255, 220, 50))
    screen.blit(txt, (screen.get_width() - txt.get_width() - 10, 10))

    dist_txt = font.render(f"Distance: {distance}", True, (255, 220, 50))
    screen.blit(dist_txt, (screen.get_width() - dist_txt.get_width() - 10, 40))

    # If game over, draw overlay and restart button
    if game_over:
        overlay = pygame.Surface(
            (screen.get_width(), screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        go_text = font.render("GAME OVER", True, (220, 40, 40))
        go_rect = go_text.get_rect(
            center=(screen.get_width()//2, screen.get_height()//2 - 20))
        screen.blit(go_text, go_rect)

        # Draw restart button
        pygame.draw.rect(screen, (200, 200, 200),
                         restart_btn_rect, border_radius=8)
        pygame.draw.rect(screen, (120, 120, 120),
                         restart_btn_rect, 3, border_radius=8)
        btn_txt = font.render("Restart", True, (20, 20, 20))
        btn_txt_rect = btn_txt.get_rect(center=restart_btn_rect.center)
        screen.blit(btn_txt, btn_txt_rect)

    pygame.display.flip()

pygame.quit()
