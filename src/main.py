import sys
import pygame

from settings import *
from game import Game
from ui import draw_grid, draw_panel, draw_start_screen, get_font


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    fonts = {
        "title": get_font(28, bold=True),
        "small": get_font(20),
        "tiny": get_font(16),
    }

    game_started = False
    game = None

    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if not game_started:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    game = Game(8, 8)
                    game_started = True
            else:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        game_started = False
                        game = None
                    elif event.key == pygame.K_r:
                        game.restart()
                    elif event.key == pygame.K_UP:
                        game.move_police(-1, 0)
                    elif event.key == pygame.K_DOWN:
                        game.move_police(1, 0)
                    elif event.key == pygame.K_LEFT:
                        game.move_police(0, -1)
                    elif event.key == pygame.K_RIGHT:
                        game.move_police(0, 1)

        if not game_started:
            draw_start_screen(screen, fonts)
        else:
            draw_grid(screen, game, fonts)
            draw_panel(screen, game, fonts)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()