from settings import window_width

# Center the camera on the player
def update_camera(player_x, screen_width):
    """
    Simple camera helper: center the camera on the player's x (return scroll x).
    Caller provides screen_width to avoid hard-coded values.
    """
    return int(player_x - (screen_width // 2))