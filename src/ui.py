import math
import pygame
from colors import *
from settings import *

FINAL_PATH_COLORS = [
    (255, 99, 132),
    (255, 159, 64),
    (255, 205, 86),
    (75, 192, 192),
    (153, 102, 255),
    (255, 105, 180),
    (0, 191, 255),
    (50, 205, 50),
]


def get_font(size, bold=False):
    preferred = ["Segoe UI", "Inter", "Calibri", "Arial"]
    return pygame.font.SysFont(preferred, size, bold=bold)


def draw_vertical_gradient(screen, top_color, bottom_color):
    width, height = screen.get_size()
    for y in range(height):
        t = y / max(1, height - 1)
        color = (
            int(top_color[0] * (1 - t) + bottom_color[0] * t),
            int(top_color[1] * (1 - t) + bottom_color[1] * t),
            int(top_color[2] * (1 - t) + bottom_color[2] * t),
        )
        pygame.draw.line(screen, color, (0, y), (width, y))


def draw_shadowed_rect(screen, rect, color, radius=16, shadow_offset=5):
    shadow_rect = rect.move(shadow_offset, shadow_offset)
    pygame.draw.rect(screen, SHADOW, shadow_rect, border_radius=radius)
    pygame.draw.rect(screen, color, rect, border_radius=radius)
    pygame.draw.rect(screen, PANEL_BORDER, rect, 2, border_radius=radius)


def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        test = word if current == "" else current + " " + word
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


def draw_wrapped_text(screen, text, font, color, x, y, max_width, max_lines, line_gap=2):
    wrapped = wrap_text(text, font, max_width)
    yy = y
    count = 0
    for line in wrapped:
        if count >= max_lines:
            break
        txt = font.render(line, True, color)
        screen.blit(txt, (x, yy))
        yy += font.get_height() + line_gap
        count += 1
    return yy


def draw_lines_block(screen, lines, font, color, x, y, max_width, max_lines_total, line_gap=2):
    yy = y
    used = 0

    for text in lines:
        wrapped = wrap_text(text, font, max_width)
        for line in wrapped:
            if used >= max_lines_total:
                return yy
            txt = font.render(line, True, color)
            screen.blit(txt, (x, yy))
            yy += font.get_height() + line_gap
            used += 1
        yy += 2

    return yy


def lerp(a, b, t):
    return a + (b - a) * t


def draw_police_icon(screen, center, radius):
    pygame.draw.circle(screen, POLICE, center, radius)
    pygame.draw.circle(screen, POLICE_DARK, center, radius, 3)

    badge_w = int(radius * 0.9)
    badge_h = int(radius * 0.45)
    badge_rect = pygame.Rect(0, 0, badge_w, badge_h)
    badge_rect.center = (center[0], center[1] + int(radius * 0.12))
    pygame.draw.rect(screen, WHITE, badge_rect, border_radius=4)
    pygame.draw.rect(screen, BLACK, badge_rect, 1, border_radius=4)

    cap_points = [
        (center[0] - int(radius * 0.8), center[1] - int(radius * 0.5)),
        (center[0] + int(radius * 0.8), center[1] - int(radius * 0.5)),
        (center[0] + int(radius * 0.45), center[1] - int(radius * 0.95)),
        (center[0] - int(radius * 0.45), center[1] - int(radius * 0.95)),
    ]
    pygame.draw.polygon(screen, POLICE_DARK, cap_points)
    pygame.draw.polygon(screen, BLACK, cap_points, 1)


def draw_bandit_icon(screen, center, radius):
    pygame.draw.circle(screen, BANDIT, center, radius)
    pygame.draw.circle(screen, BANDIT_DARK, center, radius, 3)

    eye1 = (center[0] - int(radius * 0.35), center[1] - int(radius * 0.15))
    eye2 = (center[0] + int(radius * 0.35), center[1] - int(radius * 0.15))
    pygame.draw.circle(screen, WHITE, eye1, max(2, radius // 6))
    pygame.draw.circle(screen, WHITE, eye2, max(2, radius // 6))
    pygame.draw.line(
        screen,
        BLACK,
        (center[0] - int(radius * 0.35), center[1] + int(radius * 0.3)),
        (center[0] + int(radius * 0.35), center[1] + int(radius * 0.3)),
        2,
    )


def draw_exit_icon(screen, center, radius, font):
    pygame.draw.circle(screen, EXIT, center, radius)
    pygame.draw.circle(screen, WHITE, center, max(5, radius // 2))
    txt = font.render("S", True, WHITE)
    screen.blit(txt, txt.get_rect(center=(center[0], center[1] + 1)))


def cell_rect(row, col):
    x = GRID_OFFSET_X + col * CELL_SIZE
    y = GRID_OFFSET_Y + row * CELL_SIZE
    return pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)


def cell_id(row, col, cols):
    return row * cols + col


def draw_exit(screen, exit_pos, fonts):
    r, c = exit_pos
    rect = cell_rect(r, c)
    draw_exit_icon(screen, rect.center, CELL_SIZE // 3, fonts["tiny_bold"])


def draw_grid_labels(screen, rows, cols, fonts):
    for c in range(cols):
        label = fonts["tiny"].render(str(c), True, TEXT_MUTED)
        x = GRID_OFFSET_X + c * CELL_SIZE + CELL_SIZE // 2
        y = GRID_OFFSET_Y - 18
        screen.blit(label, label.get_rect(center=(x, y)))

    for r in range(rows):
        label = fonts["tiny"].render(str(r), True, TEXT_MUTED)
        x = GRID_OFFSET_X - 16
        y = GRID_OFFSET_Y + r * CELL_SIZE + CELL_SIZE // 2
        screen.blit(label, label.get_rect(center=(x, y)))


def draw_grid(screen, game, fonts, animated_positions=None):
    draw_vertical_gradient(screen, BG_TOP, BG_BOTTOM)

    rows = len(game.grid)
    cols = len(game.grid[0])

    grid_bg = pygame.Rect(
        GRID_OFFSET_X - 18,
        GRID_OFFSET_Y - 18,
        cols * CELL_SIZE + 36,
        rows * CELL_SIZE + 36,
    )
    draw_shadowed_rect(screen, grid_bg, PANEL_BG, radius=20, shadow_offset=6)

    for r in range(rows):
        for c in range(cols):
            rect = cell_rect(r, c)
            tile = game.grid[r][c]

            color = EMPTY
            if tile == "X":
                color = WALL
            elif (r, c) == game.exit_pos:
                color = EXIT

            pygame.draw.rect(screen, color, rect, border_radius=10)
            pygame.draw.rect(screen, GRID_SOFT, rect, 1, border_radius=10)

            number_text = fonts["tiny"].render(
                str(cell_id(r, c, cols)),
                True,
                TEXT_MUTED if tile != "X" else WHITE
            )
            screen.blit(number_text, (rect.x + 5, rect.y + 4))

    if game.phase == "search":
        for pos in game.valid_ring_positions:
            if pos != game.exit_pos:
                r, c = pos
                hint = cell_rect(r, c).inflate(-20, -20)
                pygame.draw.rect(screen, VALID_RING, hint, border_radius=10)

        path = game.get_police_path()
        if path:
            for pos in path:
                if pos != game.police_pos and pos != game.exit_pos:
                    r, c = pos
                    rect = cell_rect(r, c).inflate(-26, -26)
                    pygame.draw.rect(screen, PATH_HINT, rect, border_radius=10)

    draw_exit(screen, game.exit_pos, fonts)

    if animated_positions is None:
        draw_police_at_pos(screen, game.police_pos)
        draw_bandits_at_positions(screen, game.bandits)
    else:
        draw_police_at_pixel(screen, animated_positions["police"])
        draw_bandits_at_pixels(screen, animated_positions["bandits"])

    draw_grid_labels(screen, rows, cols, fonts)


def draw_police_at_pos(screen, police_pos):
    r, c = police_pos
    rect = cell_rect(r, c)
    draw_police_icon(screen, rect.center, CELL_SIZE // 3)


def draw_bandits_at_positions(screen, bandits):
    for bandit in bandits:
        r, c = bandit
        rect = cell_rect(r, c)
        draw_bandit_icon(screen, rect.center, CELL_SIZE // 3)


def draw_police_at_pixel(screen, center):
    draw_police_icon(screen, (int(center[0]), int(center[1])), CELL_SIZE // 3)


def draw_bandits_at_pixels(screen, centers):
    for center in centers:
        draw_bandit_icon(screen, (int(center[0]), int(center[1])), CELL_SIZE // 3)


def cell_center(pos):
    r, c = pos
    rect = cell_rect(r, c)
    return rect.center


def draw_buttons(screen, buttons, fonts, game):
    mouse_pos = pygame.mouse.get_pos()

    for key, rect in buttons.items():
        if key == "graphs" and game.phase != "done":
            continue

        hover = rect.collidepoint(mouse_pos)
        fill = WHITE if not hover else (235, 242, 252)

        pygame.draw.rect(screen, SHADOW, rect.move(3, 3), border_radius=12)
        pygame.draw.rect(screen, fill, rect, border_radius=12)
        pygame.draw.rect(screen, PANEL_BORDER, rect, 2, border_radius=12)

        label = {
            "restart": "Novo mapa",
            "menu": "Menu",
            "graphs": "Gerar grafos finais",
        }[key]

        txt = fonts["small_bold"].render(label, True, TEXT)
        screen.blit(txt, txt.get_rect(center=rect.center))


def draw_panel(screen, game, fonts, buttons):
    panel_rect = pygame.Rect(PANEL_X, PANEL_Y, PANEL_WIDTH, PANEL_HEIGHT)
    draw_shadowed_rect(screen, panel_rect, PANEL_BG, radius=18, shadow_offset=5)

    title = fonts["title"].render("Police vs Bandits", True, TEXT)
    screen.blit(title, (PANEL_X + 18, PANEL_Y + 18))

    subtitle = fonts["small"].render("Distance Control", True, TEXT_SOFT)
    screen.blit(subtitle, (PANEL_X + 18, PANEL_Y + 58))

    summary = game.get_summary()

    phase_name = {
        "search": "busca da saída",
        "escape": "fuga automática",
        "done": "simulação encerrada",
    }[summary["phase"]]

    remaining = "inacessível"
    if summary["remaining_path"] is not None:
        remaining = str(summary["remaining_path"])

    info_lines = [
        f"Mapa: {summary['rows']}x{summary['cols']}",
        f"Turno: {summary['turn']}",
        f"Fase: {phase_name}",
        f"Distância escolhida: {summary['distance_value']}",
        f"Bandidos no mapa: {summary['bandits_on_map']}",
        f"Bandidos na saída: {summary['bandits_reached_exit']}",
        f"Bandidos presos: {summary['bandits_captured']}",
        f"Caminho do policial: {remaining}",
    ]

    y = PANEL_Y + 110
    for line in info_lines:
        txt = fonts["small"].render(line, True, TEXT)
        screen.blit(txt, (PANEL_X + 18, y))
        y += 26

    y += 10
    distances_title = fonts["small_bold"].render("Distâncias Atuais", True, TEXT)
    screen.blit(distances_title, (PANEL_X + 18, y))
    y += 34

    distances = game.get_current_distances_to_police()
    if not distances:
        txt = fonts["small"].render("Nenhum bandido restante.", True, TEXT_SOFT)
        screen.blit(txt, (PANEL_X + 18, y))
        y += 28
    else:
        for i, dist in enumerate(distances, start=1):
            value = "inacessível" if dist is None else str(dist)
            color = SAFE if dist == game.distance_value else WARNING
            txt = fonts["small"].render(f"Bandido {i}: {value}", True, color)
            screen.blit(txt, (PANEL_X + 18, y))
            y += 24

    y += 10
    controls_title = fonts["small_bold"].render("Controles", True, TEXT)
    screen.blit(controls_title, (PANEL_X + 18, y))
    y += 32

    controls = [
        "↑ ↓ ← → mover policial",
        "R reiniciar mapa",
        "ESC voltar ao menu",
    ]
    for line in controls:
        txt = fonts["small"].render(line, True, TEXT_SOFT)
        screen.blit(txt, (PANEL_X + 18, y))
        y += 22

    draw_buttons(screen, buttons, fonts, game)

    message_box = pygame.Rect(PANEL_X + 18, PANEL_Y + 545, PANEL_WIDTH - 36, 150)
    pygame.draw.rect(screen, CARD_BG, message_box, border_radius=14)
    pygame.draw.rect(screen, PANEL_BORDER, message_box, 2, border_radius=14)

    msg_title = fonts["small_bold"].render("Mensagem", True, TEXT)
    screen.blit(msg_title, (message_box.x + 12, message_box.y + 10))

    draw_wrapped_text(
        screen,
        game.message,
        fonts["small"],
        TEXT_SOFT,
        message_box.x + 12,
        message_box.y + 42,
        message_box.width - 24,
        5,
        line_gap=3,
    )


def draw_analysis_buttons(screen, buttons, fonts):
    mouse_pos = pygame.mouse.get_pos()

    for key, rect in buttons.items():
        hover = rect.collidepoint(mouse_pos)
        fill = WHITE if not hover else (235, 242, 252)

        pygame.draw.rect(screen, SHADOW, rect.move(3, 3), border_radius=12)
        pygame.draw.rect(screen, fill, rect, border_radius=12)
        pygame.draw.rect(screen, PANEL_BORDER, rect, 2, border_radius=12)

        label = {
            "back": "Voltar",
            "restart": "Novo mapa",
        }[key]

        txt = fonts["small_bold"].render(label, True, TEXT)
        screen.blit(txt, txt.get_rect(center=rect.center))


def draw_graph_edges_analysis(screen, game, cell, start_x, start_y):
    for r in range(len(game.grid)):
        for c in range(len(game.grid[0])):
            if game.grid[r][c] == "X":
                continue
            neighbors = []
            for nr, nc in [(r + 1, c), (r, c + 1)]:
                if 0 <= nr < len(game.grid) and 0 <= nc < len(game.grid[0]):
                    if game.grid[nr][nc] != "X":
                        neighbors.append((nr, nc))

            x1 = start_x + c * cell + cell // 2
            y1 = start_y + r * cell + cell // 2
            for nr, nc in neighbors:
                x2 = start_x + nc * cell + cell // 2
                y2 = start_y + nr * cell + cell // 2
                pygame.draw.line(screen, GRID_LINE, (x1, y1), (x2, y2), 2)


def draw_exit_analysis(screen, exit_pos, fonts, cell, start_x, start_y):
    r, c = exit_pos
    rect = pygame.Rect(start_x + c * cell, start_y + r * cell, cell, cell)
    draw_exit_icon(screen, rect.center, max(8, cell // 4), fonts["tiny_bold"])


def draw_police_analysis(screen, police_pos, cell, start_x, start_y):
    r, c = police_pos
    rect = pygame.Rect(start_x + c * cell, start_y + r * cell, cell, cell)
    draw_police_icon(screen, rect.center, max(8, cell // 4))


def draw_bandits_analysis(screen, bandits, cell, start_x, start_y):
    for bandit in bandits:
        r, c = bandit
        rect = pygame.Rect(start_x + c * cell, start_y + r * cell, cell, cell)
        draw_bandit_icon(screen, rect.center, max(8, cell // 4))


def draw_analysis_map(screen, game, fonts):
    map_rect = pygame.Rect(30, 80, 710, 480)
    draw_shadowed_rect(screen, map_rect, PANEL_BG, radius=18, shadow_offset=5)

    rows = len(game.grid)
    cols = len(game.grid[0])

    cell = min(38, min(640 // max(cols, 1), 420 // max(rows, 1)))
    start_x = 50
    start_y = 110

    for r in range(rows):
        for c in range(cols):
            rect = pygame.Rect(start_x + c * cell, start_y + r * cell, cell, cell)
            tile = game.grid[r][c]

            color = EMPTY
            if tile == "X":
                color = WALL
            elif (r, c) == game.exit_pos:
                color = EXIT

            pygame.draw.rect(screen, color, rect, border_radius=7)
            pygame.draw.rect(screen, GRID_SOFT, rect, 1, border_radius=7)

    draw_graph_edges_analysis(screen, game, cell, start_x, start_y)

    if game.final_police_path:
        for pos in game.final_police_path:
            if pos != game.exit_pos:
                r, c = pos
                rect = pygame.Rect(start_x + c * cell, start_y + r * cell, cell, cell).inflate(-16, -16)
                pygame.draw.rect(screen, POLICE, rect, border_radius=6)

    for idx, path in enumerate(game.final_bandit_paths):
        color = FINAL_PATH_COLORS[idx % len(FINAL_PATH_COLORS)]
        for pos in path:
            if pos != game.exit_pos:
                r, c = pos
                rect = pygame.Rect(start_x + c * cell, start_y + r * cell, cell, cell).inflate(-8, -8)
                pygame.draw.rect(screen, color, rect, 2, border_radius=5)

    for r in range(rows):
        for c in range(cols):
            rect = pygame.Rect(start_x + c * cell, start_y + r * cell, cell, cell)
            tile = game.grid[r][c]
            num_color = TEXT_MUTED if tile != "X" else WHITE
            number_text = fonts["tiny"].render(str(cell_id(r, c, cols)), True, num_color)
            screen.blit(number_text, (rect.x + 2, rect.y + 2))

    draw_exit_analysis(screen, game.exit_pos, fonts, cell, start_x, start_y)
    draw_police_analysis(screen, game.police_pos, cell, start_x, start_y)
    draw_bandits_analysis(screen, game.bandits, cell, start_x, start_y)


def draw_analysis_screen(screen, game, fonts, buttons, log_scroll, captured_scroll):
    draw_vertical_gradient(screen, BG_TOP, BG_BOTTOM)

    title = fonts["title_big"].render("Análise Final da Partida", True, TEXT)
    screen.blit(title, (32, 20))

    draw_analysis_map(screen, game, fonts)

    summary_rect = pygame.Rect(760, 78, 490, 215)
    draw_shadowed_rect(screen, summary_rect, PANEL_BG, radius=18, shadow_offset=5)

    summary = game.get_summary()
    summary_lines = [
        f"Tamanho do mapa: {summary['rows']}x{summary['cols']}",
        f"Turnos do policial: {summary['turn']}",
        f"Distância escolhida: {summary['distance_value']}",
        f"Caminho real: {summary['real_police_len']}",
        f"Menor caminho inicial: {summary['initial_shortest_len']}",
        f"Bandidos na saída: {summary['bandits_reached_exit']}",
        f"Bandidos presos: {summary['bandits_captured']}",
        f"Bandidos restantes: {summary['bandits_on_map']}",
    ]

    screen.blit(fonts["small_bold"].render("Resumo da Partida", True, TEXT), (780, 95))
    draw_lines_block(screen, summary_lines, fonts["small"], TEXT_SOFT, 780, 128, 440, 10, line_gap=1)

    path_rect = pygame.Rect(760, 305, 490, 155)
    draw_shadowed_rect(screen, path_rect, PANEL_BG, radius=18, shadow_offset=5)

    screen.blit(fonts["small_bold"].render("Comparação de Caminhos", True, TEXT), (780, 322))

    real_path = game.format_ids_inline(game.get_real_police_path_ids())
    shortest_initial = game.format_ids_inline(game.get_initial_shortest_path_ids())

    draw_wrapped_text(screen, f"Caminho real: {real_path}", fonts["tiny"], TEXT_SOFT, 780, 352, 450, 4, line_gap=2)
    draw_wrapped_text(screen, f"Menor caminho inicial: {shortest_initial}", fonts["tiny"], TEXT_SOFT, 780, 404, 450, 4, line_gap=2)

    captured_rect = pygame.Rect(760, 475, 490, 170)
    draw_shadowed_rect(screen, captured_rect, PANEL_BG, radius=18, shadow_offset=5)

    screen.blit(fonts["small_bold"].render("Bandidos Presos", True, TEXT), (780, 492))

    captured_lines = game.get_captured_bandits_lines()
    if not captured_lines:
        txt = fonts["small"].render("Nenhum bandido foi preso.", True, TEXT_SOFT)
        screen.blit(txt, (780, 525))
    else:
        visible_captured = 5
        captured_scroll = max(0, min(captured_scroll, max(0, len(captured_lines) - visible_captured)))
        yy = 525
        for line in captured_lines[captured_scroll:captured_scroll + visible_captured]:
            wrapped = wrap_text(line, fonts["tiny"], 450)
            for part in wrapped[:2]:
                txt = fonts["tiny"].render(part, True, TEXT_SOFT)
                screen.blit(txt, (780, yy))
                yy += 16
            yy += 4

        help2 = fonts["tiny"].render("A/D rolam a lista de presos", True, TEXT_MUTED)
        screen.blit(help2, (1040, 620))

    legend_rect = pygame.Rect(760, 660, 490, 125)
    draw_shadowed_rect(screen, legend_rect, PANEL_BG, radius=18, shadow_offset=5)

    screen.blit(fonts["small_bold"].render("Legenda", True, TEXT), (780, 676))
    screen.blit(fonts["small"].render("Azul preenchido = caminho do policial", True, POLICE), (780, 703))

    ly = 730
    for idx, _path in enumerate(game.final_bandit_paths[:3]):
        color = FINAL_PATH_COLORS[idx % len(FINAL_PATH_COLORS)]
        txt = fonts["small"].render(f"Bandido {idx + 1}", True, color)
        screen.blit(txt, (780, ly))
        ly += 22

    log_rect = pygame.Rect(30, 585, 710, 200)
    draw_shadowed_rect(screen, log_rect, PANEL_BG, radius=18, shadow_offset=5)

    screen.blit(fonts["small_bold"].render("Log Completo das Jogadas", True, TEXT), (48, 600))

    log_lines = game.get_move_log_lines()
    visible_lines = 8
    log_scroll = max(0, min(log_scroll, max(0, len(log_lines) - visible_lines)))

    yy = 632
    for line in log_lines[log_scroll:log_scroll + visible_lines]:
        wrapped = wrap_text(line, fonts["tiny"], 670)
        for part in wrapped[:2]:
            txt = fonts["tiny"].render(part, True, TEXT_SOFT)
            screen.blit(txt, (48, yy))
            yy += 16
        yy += 5

    help_txt = fonts["tiny"].render("W/S rolam o log das jogadas", True, TEXT_MUTED)
    screen.blit(help_txt, (555, 760))

    draw_analysis_buttons(screen, buttons, fonts)

    return log_scroll, captured_scroll


def draw_start_screen(screen, fonts, selected_distance, selected_bandits, selected_size, start_buttons):
    draw_vertical_gradient(screen, BG_TOP, BG_BOTTOM)

    title = fonts["title_big"].render("Police vs Bandits", True, TEXT)
    screen.blit(title, (300, 90))

    subtitle = fonts["medium"].render("Digite os parâmetros do jogo", True, TEXT_SOFT)
    screen.blit(subtitle, (420, 150))

    explanation = [
        "TAB troca o campo ativo.",
        "Digite números diretamente.",
        f"Distância máxima atual: {selected_size['max_distance']}",
        f"Máximo de bandidos atual: {selected_size['max_bandits']}",
        "ENTER inicia o jogo.",
    ]

    y = 210
    for line in explanation:
        txt = fonts["small"].render(line, True, TEXT)
        screen.blit(txt, (380, y))
        y += 28

    input_boxes = [
        ("Linhas", selected_size["rows_text"], pygame.Rect(170, 430, 180, 90), selected_size["active"] == "rows"),
        ("Colunas", selected_size["cols_text"], pygame.Rect(390, 430, 180, 90), selected_size["active"] == "cols"),
        ("Distância", selected_size["distance_text"], pygame.Rect(610, 430, 180, 90), selected_size["active"] == "distance"),
        ("Bandidos", selected_size["bandits_text"], pygame.Rect(830, 430, 180, 90), selected_size["active"] == "bandits"),
    ]

    for label, value, rect, active in input_boxes:
        shadow_rect = rect.move(4, 4)
        pygame.draw.rect(screen, SHADOW, shadow_rect, border_radius=18)

        box_color = PANEL_BG if not active else (218, 232, 250)
        pygame.draw.rect(screen, box_color, rect, border_radius=18)
        pygame.draw.rect(screen, POLICE if active else PANEL_BORDER, rect, 3 if active else 2, border_radius=18)

        label_txt = fonts["small_bold"].render(label, True, TEXT)
        screen.blit(label_txt, (rect.x + 25, rect.y + 10))

        shown_value = value if value != "" else "_"
        value_txt = fonts["title_big"].render(shown_value, True, TEXT)
        screen.blit(value_txt, value_txt.get_rect(center=(rect.centerx, rect.centery + 15)))

    hint = fonts["small"].render("Exemplos: 4x4, 5x5, 4x16, 12x16", True, TEXT_SOFT)
    screen.blit(hint, (390, 560))

    mouse_pos = pygame.mouse.get_pos()
    for key, rect in start_buttons.items():
        hover = rect.collidepoint(mouse_pos)
        fill = WHITE if not hover else (235, 242, 252)

        pygame.draw.rect(screen, SHADOW, rect.move(3, 3), border_radius=12)
        pygame.draw.rect(screen, fill, rect, border_radius=12)
        pygame.draw.rect(screen, PANEL_BORDER, rect, 2, border_radius=12)

        label = {
            "start": "Iniciar jogo",
            "quit": "Sair",
        }[key]

        txt = fonts["small_bold"].render(label, True, TEXT)
        screen.blit(txt, txt.get_rect(center=rect.center))