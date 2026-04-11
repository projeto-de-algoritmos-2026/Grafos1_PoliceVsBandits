import pygame
from colors import *
from settings import *

def get_font(size, bold=False):
    preferred = ["Segoe UI", "Inter", "Calibri", "Arial"]
    return pygame.font.SysFont(preferred, size, bold=bold)

def cell_rect(row, col):
    x = GRID_OFFSET_X + col * CELL_SIZE
    y = GRID_OFFSET_Y + row * CELL_SIZE
    return pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)


def draw_grid(screen, game, fonts):
    screen.fill(BG)

    rows = len(game.grid)
    cols = len(game.grid[0])

    for r in range(rows):
        for c in range(cols):
            rect = cell_rect(r, c)
            tile = game.grid[r][c]

            color = EMPTY
            if tile == "X":
                color = WALL
            elif (r, c) == game.exit_pos:
                color = EXIT

            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, GRID_LINE, rect, 1)

    path = game.get_police_path()
    if path:
        for pos in path:
            if pos != game.police_pos and pos != game.exit_pos:
                r, c = pos
                rect = cell_rect(r, c).inflate(-20, -20)
                pygame.draw.rect(screen, PATH_HINT, rect)

    draw_police(screen, game.police_pos)
    draw_exit(screen, game.exit_pos, fonts)


def draw_police(screen, police_pos):
    r, c = police_pos
    rect = cell_rect(r, c)
    pygame.draw.circle(screen, POLICE, rect.center, CELL_SIZE // 3)


def draw_exit(screen, exit_pos, fonts):
    r, c = exit_pos
    rect = cell_rect(r, c)
    txt = fonts["tiny"].render("S", True, WHITE)
    screen.blit(txt, txt.get_rect(center=rect.center))


def draw_panel(screen, game, fonts):
    panel_rect = pygame.Rect(PANEL_X, PANEL_Y, PANEL_WIDTH, PANEL_HEIGHT)
    pygame.draw.rect(screen, PANEL_BG, panel_rect)
    pygame.draw.rect(screen, GRID_LINE, panel_rect, 2)

    title = fonts["title"].render("Police vs Bandits", True, TEXT)
    screen.blit(title, (PANEL_X + 16, PANEL_Y + 16))

    summary = game.get_summary()
    lines = [
        f"Mapa: {summary['rows']}x{summary['cols']}",
        f"Turno: {summary['turn']}",
        f"Caminho restante: {summary['remaining_path']}",
        "",
        game.message,
    ]

    y = PANEL_Y + 70
    for line in lines:
        txt = fonts["small"].render(str(line), True, TEXT)
        screen.blit(txt, (PANEL_X + 16, y))
        y += 28


def draw_start_screen(screen, fonts):
    screen.fill(BG)
    title = fonts["title"].render("Police vs Bandits", True, TEXT)
    subtitle = fonts["small"].render("Pressione ENTER para iniciar", True, TEXT)
    screen.blit(title, (430, 280))
    screen.blit(subtitle, (430, 330))