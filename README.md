# Platform Gimma

An endless 2D platformer built with Python and Pygame. Run and jump across randomly generated ice platforms, collect fish, and avoid the orcas. When you die you get one last chance: if you have at least 5 fish, you can spend them on a round of blackjack to earn a second life.

## Gameplay

- Platforms are generated as you go, sometimes with a second platform above the main one
- **Fish** are the coins: each one adds 1 to your score
- **Orcas** end your run on contact, and so does falling off the screen
- With **5 or more fish** when you die, you can play a blackjack minigame for 5 fish. Win, and you keep playing
- After game over, click to start a new run

## Controls

| Key | Action |
| --- | --- |
| `A` / `←` | Move left |
| `D` / `→` | Move right |
| `Space` | Jump (press again in the air to double jump) |
| `H` | Hit (blackjack) |
| `S` | Stand (blackjack) |

## Running it

Requires Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install pygame
python main.py
```

Run it from the project folder, since the sprites and card images are loaded from `images/`.

## Project layout

```
main.py       game loop, coins, orcas, score and the blackjack minigame
player.py     player sprite, movement, double jump and animation
platforms.py  platform generation and drawing
blackjack.py  deck, hand values and card images
settings.py   tuning: gravity, jump strength, platform sizes and gaps
images/       hero animation frames, fish, background and playing cards
```

Want to change how the game feels? Most of it is in `settings.py`: try `gravity`, `player_jump_strength` or `player_max_jumps`.

## Credits

Built by [WesleyVeeningen](https://github.com/WesleyVeeningen) and [Yeltkat](https://github.com/Yeltkat).
