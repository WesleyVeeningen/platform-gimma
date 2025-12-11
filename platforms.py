import random
import pygame
from settings import color_platform

# ----------------------------------------------------------
# Create a batch of random platforms for the start of the game
# ----------------------------------------------------------
def generate_initial_platforms(amount_of_platforms, min_gap, max_gap,
                               min_width, max_width, base_y, double_chance):
    platform_list = []
    current_x_position = 0

    for i in range(amount_of_platforms):
        # --- Main platform values ---
        main_width = random.randint(min_width, max_width)
        main_height = 40
        main_y_position = base_y

        # ensure the very first platform ALWAYS starts at x = 0 (left edge)
        if i == 0:
            new_x = 0
        else:
            gap = random.randint(min_gap, max_gap)
            new_x = current_x_position + gap

        new_platform = pygame.Rect(new_x, main_y_position, main_width, main_height)
        platform_list.append(new_platform)
        current_x_position = new_platform.x + new_platform.width

        # optionally add an upper platform relative to this main platform
        if random.random() < double_chance:
            upper_y_position = main_y_position - random.randint(100, 180)
            upper_width = random.randint(min_width // 2, min_width)

            # safe horizontal offset calculation (center if no room)
            left = 20
            right = main_width - upper_width - 20
            if right < left:
                offset = max(0, (main_width - upper_width) // 2)
            else:
                offset = random.randint(left, right)

            upper_platform = pygame.Rect(new_x + offset, upper_y_position, upper_width, main_height)
            platform_list.append(upper_platform)

    return platform_list

# ----------------------------------------------------------
# Add more platforms when camera approaches the end
# ----------------------------------------------------------
def extend_platforms_if_needed(platform_list, camera_scroll_x, screen_width,
                               min_gap, max_gap, min_width, max_width,
                               base_y, double_chance):

    if not platform_list:
        return

    last_platform = platform_list[-1]
    last_end_x = last_platform.x + last_platform.width

    # extend when camera is near the end
    if camera_scroll_x + screen_width + 300 > last_end_x:

        main_width = random.randint(min_width, max_width)
        gap = random.randint(min_gap, max_gap)
        y_offset_main = random.randint(-80, 80)
        main_y_position = base_y + y_offset_main

        new_platform_x = last_end_x + gap
        main_height = 40

        # Main platform
        main_platform = pygame.Rect(
            new_platform_x,
            main_y_position,
            main_width,
            main_height
        )
        platform_list.append(main_platform)

        # Optional double path
        if random.random() < double_chance:
            upper_y_position = main_y_position - random.randint(100, 180)
            upper_width = random.randint(min_width // 2, min_width)

            left = 20
            right = main_width - upper_width - 20
            if right < left:
                offset = max(0, (main_width - upper_width) // 2)
            else:
                offset = random.randint(left, right)

            upper_platform = pygame.Rect(
                new_platform_x + offset,
                upper_y_position,
                upper_width,
                main_height
            )
            platform_list.append(upper_platform)


# ----------------------------------------------------------
# Draw platforms with camera scrolling
# ----------------------------------------------------------
def draw_platforms(screen, camera_scroll_x, platform_list):
    for platform_rect in platform_list:
        pygame.draw.rect(
            screen,
            color_platform,
            pygame.Rect(
                platform_rect.x - camera_scroll_x,
                platform_rect.y,
                platform_rect.width,
                platform_rect.height
            )
        )
