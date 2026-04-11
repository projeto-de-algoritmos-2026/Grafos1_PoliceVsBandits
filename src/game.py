from graph_utils import shortest_path
from map_generator import generate_valid_map


class Game:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.turn = 0
        self.message = "Encontre a saída."
        self.generate_new_game()

    def generate_new_game(self):
        self.grid, self.police_pos, self.exit_pos = generate_valid_map(
            self.rows, self.cols
        )
        self.turn = 0
        self.message = "Encontre a saída."

    def restart(self):
        self.generate_new_game()

    def pos_to_id(self, pos):
        r, c = pos
        return r * self.cols + c

    def path_to_ids(self, path):
        return [self.pos_to_id(p) for p in path]

    def format_ids_inline(self, ids_list):
        return " → ".join(str(x) for x in ids_list)

    def is_valid(self, pos):
        r, c = pos
        return (
            0 <= r < len(self.grid)
            and 0 <= c < len(self.grid[0])
            and self.grid[r][c] != "X"
        )

    def get_police_path(self):
        path, _ = shortest_path(self.grid, self.police_pos, self.exit_pos)
        return path

    def move_police(self, dr, dc):
        nr = self.police_pos[0] + dr
        nc = self.police_pos[1] + dc
        new_pos = (nr, nc)

        if not self.is_valid(new_pos):
            self.message = "Movimento inválido."
            return False

        self.police_pos = new_pos
        self.turn += 1

        if self.police_pos == self.exit_pos:
            self.message = "Você encontrou a saída!"
            return True

        path, dist = shortest_path(self.grid, self.police_pos, self.exit_pos)
        if path and dist is not None:
            self.message = f"Turno {self.turn}. Menor caminho restante: {dist}."
        else:
            self.message = "Não existe caminho até a saída."
        return True

    def get_summary(self):
        path, dist = shortest_path(self.grid, self.police_pos, self.exit_pos)
        return {
            "turn": self.turn,
            "rows": self.rows,
            "cols": self.cols,
            "remaining_path": dist,
            "phase": "search",
            "distance_value": "-",
            "bandits_on_map": 0,
            "bandits_reached_exit": 0,
            "bandits_captured": 0,
        }

    def get_current_distances_to_police(self):
        return []

    def get_real_police_path_ids(self):
        return [self.pos_to_id(self.police_pos)]

    def get_initial_shortest_path_ids(self):
        path = self.get_police_path()
        return self.path_to_ids(path) if path else []

    def get_move_log_lines(self):
        return []

    def get_captured_bandits_lines(self):
        return []

    in_analysis_screen = False
    phase = "search"
    bandits = []
    valid_ring_positions = []