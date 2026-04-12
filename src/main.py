import sys
import pygame

from settings import *
from colors import *
from game import Game
from ui import (
    draw_grid,
    draw_panel,
    draw_start_screen,
    draw_analysis_screen,
    get_font,
    cell_center,
)


def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


def safe_int(text, default):
    try:
        return int(text)
    except ValueError:
        return default


def compute_limits(rows, cols):
    area = rows * cols
    max_distance = max(1, min(rows + cols - 2, area // 3))
    max_bandits = max(1, min(area // 4, 12))
    return max_distance, max_bandits


def sanitize_inputs(rows_text, cols_text, dist_text, bandits_text):
    rows = clamp(safe_int(rows_text, 8), 4, 20)
    cols = clamp(safe_int(cols_text, 8), 4, 20)

    max_distance, max_bandits = compute_limits(rows, cols)

    distance = clamp(safe_int(dist_text, 3), 1, max_distance)
    bandits = clamp(safe_int(bandits_text, 3), 1, max_bandits)

    return rows, cols, distance, bandits, max_distance, max_bandits


def handle_text_input(current_text, event, max_len=3):
    if event.key == pygame.K_BACKSPACE:
        return current_text[:-1]

    if event.unicode.isdigit():
        if len(current_text) < max_len:
            return current_text + event.unicode

    return current_text


def build_animation_state(game):
    return {
        "active": False,
        "timer": 0,
        "duration": 180,
        "police_from": None,
        "police_to": None,
        "bandits_from": [],
        "bandits_to": [],
    }


def start_animation(anim, old_police, new_police, old_bandits, new_bandits):
    anim["active"] = True
    anim["timer"] = 0
    anim["police_from"] = old_police
    anim["police_to"] = new_police
    anim["bandits_from"] = old_bandits[:]
    anim["bandits_to"] = new_bandits[:]


def get_animated_positions(anim):
    if not anim["active"]:
        return None

    t = min(1.0, anim["timer"] / max(1, anim["duration"]))
    ease = 1 - (1 - t) * (1 - t)

    pf = cell_center(anim["police_from"])
    pt = cell_center(anim["police_to"])
    police_center = (
        pf[0] + (pt[0] - pf[0]) * ease,
        pf[1] + (pt[1] - pf[1]) * ease,
    )

    bandit_centers = []
    count = min(len(anim["bandits_from"]), len(anim["bandits_to"]))
    for i in range(count):
        bf = cell_center(anim["bandits_from"][i])
        bt = cell_center(anim["bandits_to"][i])
        bandit_centers.append((
            bf[0] + (bt[0] - bf[0]) * ease,
            bf[1] + (bt[1] - bf[1]) * ease,
        ))

    for i in range(count, len(anim["bandits_to"])):
        bandit_centers.append(cell_center(anim["bandits_to"][i]))

    return {
        "police": police_center,
        "bandits": bandit_centers,
    }


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    fonts = {
        "title": get_font(30, bold=True),
        "title_big": get_font(42, bold=True),
        "medium": get_font(24, bold=True),
        "small": get_font(20),
        "small_bold": get_font(20, bold=True),
        "tiny": get_font(14),
        "tiny_bold": get_font(14, bold=True),
    }

    start_buttons = {
        "start": pygame.Rect(430, 700, 240, 52),
        "quit": pygame.Rect(690, 700, 180, 52),
    }

    game_buttons = {
        "restart": pygame.Rect(PANEL_X + 18, PANEL_Y + 475, 145, 44),
        "menu": pygame.Rect(PANEL_X + 180, PANEL_Y + 475, 145, 44),
        "graphs": pygame.Rect(PANEL_X + 18, PANEL_Y + 430, 307, 38),
    }

    analysis_buttons = {
        "back": pygame.Rect(1030, 20, 100, 38),
        "restart": pygame.Rect(1140, 20, 110, 38),
    }

    game_started = False
    game = None

    auto_escape_timer = 0
    auto_escape_delay = 280
    log_scroll = 0
    captured_scroll = 0

    fields = ["rows", "cols", "distance", "bandits"]
    active_field_index = 0

    rows_text = "8"
    cols_text = "8"
    distance_text = "3"
    bandits_text = "3"

    animation = build_animation_state(None)

    running = True
    while running:
        dt = clock.tick(FPS)

        if animation["active"]:
            animation["timer"] += dt
            if animation["timer"] >= animation["duration"]:
                animation["active"] = False

        if game_started and game is not None and game.phase == "escape":
            auto_escape_timer += dt
            if auto_escape_timer >= auto_escape_delay:
                old_bandits = game.bandits[:]
                changed = game.update_escape()
                auto_escape_timer = 0
                if changed:
                    # anima só bandido na fuga automática
                    animation["active"] = True
                    animation["timer"] = 0
                    animation["duration"] = 180
                    animation["police_from"] = game.police_pos
                    animation["police_to"] = game.police_pos
                    animation["bandits_from"] = old_bandits[:]
                    animation["bandits_to"] = game.bandits[:]

        rows, cols, distance, bandits, max_distance, max_bandits = sanitize_inputs(
            rows_text, cols_text, distance_text, bandits_text
        )

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if not game_started:
                if event.type == pygame.KEYDOWN:
                    active_field = fields[active_field_index]

                    if event.key == pygame.K_TAB:
                        active_field_index = (active_field_index + 1) % len(fields)

                    elif event.key == pygame.K_RETURN:
                        game = Game(distance, bandits, rows, cols)
                        game_started = True
                        auto_escape_timer = 0
                        log_scroll = 0
                        captured_scroll = 0
                        animation = build_animation_state(game)

                    else:
                        if active_field == "rows":
                            rows_text = handle_text_input(rows_text, event)
                        elif active_field == "cols":
                            cols_text = handle_text_input(cols_text, event)
                        elif active_field == "distance":
                            distance_text = handle_text_input(distance_text, event)
                        elif active_field == "bandits":
                            bandits_text = handle_text_input(bandits_text, event)

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    pos = event.pos

                    input_rects = {
                        "rows": pygame.Rect(170, 430, 180, 90),
                        "cols": pygame.Rect(390, 430, 180, 90),
                        "distance": pygame.Rect(610, 430, 180, 90),
                        "bandits": pygame.Rect(830, 430, 180, 90),
                    }

                    for i, field in enumerate(fields):
                        if input_rects[field].collidepoint(pos):
                            active_field_index = i

                    if start_buttons["start"].collidepoint(pos):
                        game = Game(distance, bandits, rows, cols)
                        game_started = True
                        auto_escape_timer = 0
                        log_scroll = 0
                        captured_scroll = 0
                        animation = build_animation_state(game)
                    elif start_buttons["quit"].collidepoint(pos):
                        running = False

            else:
                if game.in_analysis_screen:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_w:
                            log_scroll = max(0, log_scroll - 1)
                        elif event.key == pygame.K_s:
                            log_scroll += 1
                        elif event.key == pygame.K_a:
                            captured_scroll = max(0, captured_scroll - 1)
                        elif event.key == pygame.K_d:
                            captured_scroll += 1
                        elif event.key == pygame.K_ESCAPE:
                            game.exit_analysis_screen()

                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        pos = event.pos
                        if analysis_buttons["back"].collidepoint(pos):
                            game.exit_analysis_screen()
                        elif analysis_buttons["restart"].collidepoint(pos):
                            game.restart()
                            auto_escape_timer = 0
                            log_scroll = 0
                            captured_scroll = 0
                            animation = build_animation_state(game)

                else:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            game_started = False
                            game = None
                        elif event.key == pygame.K_r:
                            game.restart()
                            auto_escape_timer = 0
                            log_scroll = 0
                            captured_scroll = 0
                            animation = build_animation_state(game)
                        elif game.phase == "search" and not animation["active"]:
                            old_police = game.police_pos
                            old_bandits = game.bandits[:]

                            moved = False
                            if event.key == pygame.K_UP:
                                moved = game.move_police(-1, 0)
                            elif event.key == pygame.K_DOWN:
                                moved = game.move_police(1, 0)
                            elif event.key == pygame.K_LEFT:
                                moved = game.move_police(0, -1)
                            elif event.key == pygame.K_RIGHT:
                                moved = game.move_police(0, 1)

                            if moved:
                                start_animation(
                                    animation,
                                    old_police,
                                    game.police_pos,
                                    old_bandits,
                                    game.bandits,
                                )

                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        pos = event.pos
                        if game_buttons["restart"].collidepoint(pos):
                            game.restart()
                            auto_escape_timer = 0
                            log_scroll = 0
                            captured_scroll = 0
                            animation = build_animation_state(game)
                        elif game_buttons["menu"].collidepoint(pos):
                            game_started = False
                            game = None
                        elif game_buttons["graphs"].collidepoint(pos):
                            game.generate_final_graphs()
                            log_scroll = 0
                            captured_scroll = 0

        if not game_started:
            draw_start_screen(
                screen=screen,
                fonts=fonts,
                selected_distance=distance,
                selected_bandits=bandits,
                selected_size={
                    "rows_text": rows_text,
                    "cols_text": cols_text,
                    "distance_text": distance_text,
                    "bandits_text": bandits_text,
                    "active": fields[active_field_index],
                    "max_distance": max_distance,
                    "max_bandits": max_bandits,
                },
                start_buttons=start_buttons,
            )
        else:
            if game.in_analysis_screen:
                log_scroll, captured_scroll = draw_analysis_screen(
                    screen, game, fonts, analysis_buttons, log_scroll, captured_scroll
                )
            else:
                animated_positions = get_animated_positions(animation) if animation["active"] else None
                draw_grid(screen, game, fonts, animated_positions=animated_positions)
                draw_panel(screen, game, fonts, game_buttons)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()