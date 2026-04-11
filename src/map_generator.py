import random
from graph_utils import shortest_path


def random_empty_grid(rows, cols, wall_probability=0.16):
    grid = []

    for _ in range(rows):
        row = []
        for _ in range(cols):
            if random.random() < wall_probability:
                row.append("X")
            else:
                row.append(".")
        grid.append(row)

    return grid


def random_free_cell(grid):
    free_cells = []

    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] == ".":
                free_cells.append((r, c))

    return random.choice(free_cells) if free_cells else None


def generate_valid_map(rows, cols, max_attempts=1000):
    for _ in range(max_attempts):
        grid = random_empty_grid(rows, cols)

        police = random_free_cell(grid)
        exit_pos = random_free_cell(grid)

        if police is None or exit_pos is None:
            continue

        if police == exit_pos:
            continue

        path, dist = shortest_path(grid, police, exit_pos)
        if not path or dist is None:
            continue

        grid[exit_pos[0]][exit_pos[1]] = "E"
        return grid, police, exit_pos

    raise RuntimeError("Não foi possível gerar um mapa válido.")