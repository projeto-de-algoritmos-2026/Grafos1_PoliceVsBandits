import random
from graph_utils import bfs_distances, shortest_path
from map_generator import generate_valid_map


class Game:
    def __init__(self, distance_value, num_bandits, rows, cols):
        self.distance_value = distance_value
        self.num_bandits = num_bandits
        self.rows = rows
        self.cols = cols

        self.turn = 0
        self.phase = "search"
        self.message = ""
        self.bandits = []
        self.valid_ring_positions = []

        self.police_history = []
        self.initial_shortest_path = []

        self.generate_new_game()

    def generate_new_game(self):
        self.grid, self.police_pos, self.exit_pos = generate_valid_map(
            self.rows, self.cols
        )

        self.turn = 0
        self.phase = "search"
        self.message = "Encontre a saída."

        self.update_valid_ring()
        self.bandits = self.spawn_bandits()

        self.police_history = [self.police_pos]

        path, _ = shortest_path(self.grid, self.police_pos, self.exit_pos)
        self.initial_shortest_path = path[:] if path else []

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

    def update_valid_ring(self):
        distances, _ = bfs_distances(self.grid, self.police_pos)
        self.valid_ring_positions = [
            pos for pos, d in distances.items()
            if d == self.distance_value and pos != self.exit_pos
        ]

    def spawn_bandits(self):
        candidates = self.valid_ring_positions[:]
        random.shuffle(candidates)
        return candidates[: self.num_bandits]

    def move_police(self, dr, dc):
        if self.phase != "search":
            return False

        nr = self.police_pos[0] + dr
        nc = self.police_pos[1] + dc
        new_pos = (nr, nc)

        if not self.is_valid(new_pos):
            self.message = "Movimento inválido."
            return False

        self.police_pos = new_pos
        self.turn += 1
        self.police_history.append(self.police_pos)

        if self.police_pos == self.exit_pos:
            self.message = "Você encontrou a saída!"
            self.phase = "done"
            return True

        self.update_valid_ring()

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
            "phase": self.phase,
            "distance_value": self.distance_value,
            "bandits_on_map": len(self.bandits),
            "bandits_reached_exit": 0,
            "bandits_captured": 0,
        }

    def get_current_distances_to_police(self):
        distances, _ = bfs_distances(self.grid, self.police_pos)
        return [distances.get(b, None) for b in self.bandits]

    def get_real_police_path_ids(self):
        return self.path_to_ids(self.police_history)

    def get_initial_shortest_path_ids(self):
        return self.path_to_ids(self.initial_shortest_path)

    def get_move_log_lines(self):
        return []

    def get_captured_bandits_lines(self):
        return []

    in_analysis_screen = False