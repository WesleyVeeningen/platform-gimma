import pygame
import os
from settings import gravity, player_jump_strength, player_move_speed, player_width, player_height, color_player, player_max_jumps

class Player(pygame.sprite.Sprite):
    def __init__(self, x=200, y=300):
        pygame.sprite.Sprite.__init__(self)

        # try to load images, otherwise use a colored rect
        raw_images = []
        for i in range(1, 9):
            path = os.path.join('images', 'hero' + str(i) + '.png')
            try:
                img = pygame.image.load(path).convert_alpha()
                raw_images.append(img)
            except Exception:
                # image missing -> continue (we'll use fallback surface)
                pass

        # animation frames (scaled)
        if raw_images:
            self.anim_frames = [
                pygame.transform.scale(img, (player_width, player_height)).convert_alpha()
                for img in raw_images
            ]
        else:
            surf = pygame.Surface((player_width, player_height), pygame.SRCALPHA)
            surf.fill(color_player)
            self.anim_frames = [surf]

        # animation state
        self.anim_index = 0
        self.anim_delay_ms = 80
        self.last_anim_time = pygame.time.get_ticks()

        # facing / movement
        self.facing_right = True

        # start image & rect
        self.image = self.anim_frames[0]
        self.rect = self.image.get_rect()

        # world coordinates
        self.x = x
        self.y = y
        self.vel_y = 0
        self.on_ground = False

        # horizontal velocity for momentum (so stopping while walking doesn't
        # instantly stop the player mid-air)
        self.vel_x = 0.0
        # tuning: higher ground friction = stop faster on ground; air friction
        # close to 1.0 means slower bleed-off in air
        self._ground_friction = 0.5
        self._air_friction = 0.985
        # how fast velocity approaches target when input is held (less in air)
        self._ground_accel = 1.0
        self._air_accel = 0.35

        # double-jump state
        self.max_jumps = player_max_jumps
        self.jumps_left = self.max_jumps
        self.jump_pressed_last = False

        # --- reduced collision hitbox (anchored to sprite bottom) ---
        # make collision box slightly smaller than the visible sprite so the
        # player can fit under low platforms and have a more forgiving hitbox.
        self.cw = max(8, player_width - 12)   # collision width
        self.ch = max(8, player_height - 10)  # collision height
        # offset so collision box is centered horizontally and anchored to bottom
        self.c_offset_x = (player_width - self.cw) / 2.0
        self.c_offset_y = (player_height - self.ch)

    def _update_animation(self, moving):
        now = pygame.time.get_ticks()
        if moving:
            if now - self.last_anim_time >= self.anim_delay_ms:
                self.anim_index = (self.anim_index + 1) % len(self.anim_frames)
                self.last_anim_time = now
        else:
            # idle -> reset to first frame
            self.anim_index = 0

        frame = self.anim_frames[self.anim_index]
        if not self.facing_right:
            frame = pygame.transform.flip(frame, True, False)
        # update image and rect size (keep topleft after)
        prev_topleft = getattr(self, "rect", pygame.Rect(0, 0, 0, 0)).topleft
        self.image = frame
        self.rect = self.image.get_rect()
        self.rect.topleft = prev_topleft

    def update(self, platforms, camera_scroll_x):
        # horizontal momentum handling: vel_x persists and decays differently
        # on ground vs in air so player doesn't snap to a stop mid-air.
        keys = pygame.key.get_pressed()

        # remember previous position for collision direction checks
        prev_x = self.x
        prev_y = self.y

        # INPUT: determine desired horizontal speed from keys
        desired = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            desired = -player_move_speed
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            desired = player_move_speed

        # choose accel depending on whether we are on the ground
        accel = self._ground_accel if self.on_ground else self._air_accel

        # If there's input, move vel_x toward desired target.
        # If no horizontal input, only apply friction (don't pull vel toward 0 again)
        if desired != 0:
            self.vel_x += (desired - self.vel_x) * accel
        else:
            if self.on_ground:
                self.vel_x *= self._ground_friction
                # snap to zero to avoid tiny drift
                if abs(self.vel_x) < 0.2:
                    self.vel_x = 0.0
            else:
                # in air: very light damping so momentum persists longer
                self.vel_x *= 0.993

        # apply horizontal movement
        self.x += self.vel_x

        moving = abs(self.vel_x) > 0.3

        # Horizontal collision resolution (prevent moving into platform sides)
        # use the reduced collision rect (world coords)
        horiz_rect = pygame.Rect(int(self.x + self.c_offset_x), int(self.y + self.c_offset_y), int(self.cw), int(self.ch))
        for plat in platforms:
            if horiz_rect.colliderect(plat):
                # Only treat this as a side collision if there's vertical overlap
                vertical_overlap = not (horiz_rect.bottom <= plat.y or horiz_rect.top >= (plat.y + plat.height))
                if vertical_overlap:
                    # collided horizontally: push back to previous safe position
                    if prev_x < self.x:
                        # moving right -> place to left of platform
                        self.x = plat.x - player_width
                    elif prev_x > self.x:
                        # moving left -> place to right of platform
                        self.x = plat.x + plat.width
                    # update horiz_rect to new position
                    horiz_rect.x = int(self.x + self.c_offset_x)

        # Apply gravity (vertical movement)
        self.vel_y += gravity
        self.y += self.vel_y

        # Vertical collision resolution using previous Y to detect coming-from-above
        self.on_ground = False
        vert_rect = pygame.Rect(int(self.x + self.c_offset_x), int(self.y + self.c_offset_y), int(self.cw), int(self.ch))
        for plat in platforms:
            if vert_rect.colliderect(plat):
                # coming down onto platform (allow 1 px tolerance to avoid tunneling)
                prev_collision_bottom = prev_y + self.c_offset_y + self.ch
                if prev_collision_bottom <= plat.y + 1:
                    # snap sprite so its feet rest on platform (top of sprite = platform.y - sprite_height)
                    self.y = plat.y - player_height
                    self.vel_y = 0
                    self.on_ground = True
                    # reset jumps when landing
                    self.jumps_left = self.max_jumps
                # hitting head on underside of platform
                elif prev_y >= plat.y + plat.height:
                    self.y = plat.y + plat.height
                    self.vel_y = 0
                vert_rect.y = int(self.y + self.c_offset_y)

        # Jump (edge-detect space so holding doesn't repeatedly trigger)
        jump_pressed = keys[pygame.K_SPACE]
        if jump_pressed and not self.jump_pressed_last and self.jumps_left > 0:
            self.vel_y = player_jump_strength
            self.jumps_left -= 1
            self.on_ground = False
        self.jump_pressed_last = jump_pressed

        # Animation update (use moving flag)
        self._update_animation(moving)

        # Update sprite rect for rendering (screen coordinates)
        # rendering still uses full sprite size; camera offset applied here by caller
        self.rect.topleft = (int(self.x - camera_scroll_x), int(self.y))

