import random
from graph_utils import bfs_distances, shortest_path, get_neighbors
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
        self.bandit_paths = []
        self.valid_ring_positions = []
        self.bandits_reached_exit = 0
        self.bandits_captured = 0

        self.bandits = []
        self.police_history = []
        self.bandit_history = []
        self.move_log = []
        self.captured_bandits_log = []
        self.initial_shortest_path = []

        self.generate_new_game()

    def generate_new_game(self):
        self.grid, self.police_pos, self.exit_pos = generate_valid_map(
            self.rows, self.cols
        )

        self.turn = 0
        self.phase = "search"
        self.message = "Encontre a saída."
        self.bandit_paths = []
        self.bandits_reached_exit = 0
        self.bandits_captured = 0

        self.update_valid_ring()
        self.bandits = self.spawn_bandits()

        self.police_history = [self.police_pos]
        self.bandit_history = [[b] for b in self.bandits]
        self.move_log = []
        self.captured_bandits_log = []

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

    def get_real_police_path_ids(self):
        return self.path_to_ids(self.police_history)

    def get_initial_shortest_path_ids(self):
        return self.path_to_ids(self.initial_shortest_path)

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

    def _candidate_bandit_moves(self, bandit_pos):
        candidates = [bandit_pos]
        for neighbor in get_neighbors(self.grid, bandit_pos):
            if neighbor != self.exit_pos:
                candidates.append(neighbor)

        unique = []
        seen = set()
        for pos in candidates:
            if pos not in seen:
                unique.append(pos)
                seen.add(pos)
        return unique

    def reposition_bandits(self):
        distances_from_police, _ = bfs_distances(self.grid, self.police_pos)

        new_bandits = []
        new_histories = []
        occupied = set()
        captured_now = 0

        for i, bandit in enumerate(self.bandits):
            history = self.bandit_history[i][:]
            local_moves = self._candidate_bandit_moves(bandit)

            valid_local_moves = []
            for pos in local_moves:
                d = distances_from_police.get(pos, None)
                if d == self.distance_value and pos != self.exit_pos:
                    valid_local_moves.append(pos)

            valid_local_moves = [pos for pos in valid_local_moves if pos not in occupied]

            if not valid_local_moves:
                captured_now += 1
                self.captured_bandits_log.append({
                    "bandit_index": i + 1,
                    "turn": self.turn,
                    "vertex_id": self.pos_to_id(bandit),
                    "reason": "encurralado sem movimento local válido na distância exata",
                })
                continue

            best = min(
                valid_local_moves,
                key=lambda p: (
                    abs(p[0] - bandit[0]) + abs(p[1] - bandit[1]),
                    self.pos_to_id(p),
                ),
            )

            occupied.add(best)
            new_bandits.append(best)
            history.append(best)
            new_histories.append(history)

        self.bandits = new_bandits
        self.bandit_history = new_histories
        self.bandits_captured += captured_now
        self.update_valid_ring()

    def register_move_log(self, old_pos, new_pos):
        shortest_now, _ = shortest_path(self.grid, new_pos, self.exit_pos)
        old_shortest, _ = shortest_path(self.grid, old_pos, self.exit_pos)

        optimal_move = False
        if old_shortest and len(old_shortest) >= 2:
            optimal_move = old_shortest[1] == new_pos

        self.move_log.append({
            "step": len(self.move_log) + 1,
            "from_id": self.pos_to_id(old_pos),
            "to_id": self.pos_to_id(new_pos),
            "shortest_path_ids": self.path_to_ids(shortest_now) if shortest_now else [],
            "shortest_path_len": max(0, len(shortest_now) - 1) if shortest_now else -1,
            "optimal": optimal_move,
        })

    def move_police(self, dr, dc):
        if self.phase != "search":
            return False

        old_pos = self.police_pos
        nr = self.police_pos[0] + dr
        nc = self.police_pos[1] + dc
        new_pos = (nr, nc)

        if not self.is_valid(new_pos):
            self.message = "Movimento inválido."
            return False

        self.police_pos = new_pos
        self.turn += 1
        self.police_history.append(self.police_pos)
        self.register_move_log(old_pos, new_pos)

        if self.police_pos == self.exit_pos:
            self.start_escape_phase()
            return True

        self.reposition_bandits()

        path = self.get_police_path()
        if path:
            self.message = f"Turno {self.turn}. Menor caminho restante até a saída: {len(path) - 1}."
        else:
            self.message = "A saída ficou inacessível a partir da posição atual."
        return True

    def start_escape_phase(self):
        self.phase = "escape"
        self.message = "Saída encontrada. Os bandidos restantes estão fugindo automaticamente."

        self.bandit_paths = []
        survivors = []
        survivor_history = []

        for i, bandit in enumerate(self.bandits):
            path, dist = shortest_path(self.grid, bandit, self.exit_pos)
            if path and dist is not None:
                self.bandit_paths.append(path[:])
                survivors.append(bandit)
                survivor_history.append(self.bandit_history[i])
            else:
                self.bandits_captured += 1

        self.bandits = survivors
        self.bandit_history = survivor_history

        if not self.bandits:
            self.phase = "done"
            self.message = "Fim da simulação. Nenhum bandido restante conseguiu rota até a saída."

    def update_escape(self):
        if self.phase != "escape":
            return False

        occupied_next = set()
        new_bandits = []
        new_paths = []
        new_histories = []

        for i, path in enumerate(self.bandit_paths):
            current_pos = path[0]
            history = self.bandit_history[i]

            if len(path) > 1:
                candidate_next = path[1]

                if candidate_next == self.exit_pos:
                    self.bandits_reached_exit += 1
                    history.append(self.exit_pos)
                    continue

                if candidate_next not in occupied_next:
                    path.pop(0)
                    current_pos = path[0]

            if current_pos != self.exit_pos:
                occupied_next.add(current_pos)
                new_bandits.append(current_pos)
                new_paths.append(path)
                history.append(current_pos)
                new_histories.append(history)

        self.bandits = new_bandits
        self.bandit_paths = new_paths
        self.bandit_history = new_histories

        if not self.bandits:
            self.phase = "done"
            self.message = "Fim da simulação."
        return True

    def get_summary(self):
        police_path = self.get_police_path()
        remaining = None if not police_path else len(police_path) - 1

        return {
            "turn": self.turn,
            "rows": self.rows,
            "cols": self.cols,
            "remaining_path": remaining,
            "phase": self.phase,
            "distance_value": self.distance_value,
            "bandits_on_map": len(self.bandits),
            "bandits_reached_exit": self.bandits_reached_exit,
            "bandits_captured": self.bandits_captured,
        }

    def get_current_distances_to_police(self):
        distances, _ = bfs_distances(self.grid, self.police_pos)
        return [distances.get(b, None) for b in self.bandits]

    def get_move_log_lines(self):
        lines = []
        for item in self.move_log:
            path_str = " → ".join(str(x) for x in item["shortest_path_ids"])
            status = "ótima" if item["optimal"] else "desvio"
            lines.append(
                f"{item['step']}. {item['from_id']} → {item['to_id']} | "
                f"{status} | tam={item['shortest_path_len']} | menor caminho: {path_str}"
            )
        return lines

    def get_captured_bandits_lines(self):
        lines = []
        for item in self.captured_bandits_log:
            lines.append(
                f"Bandido {item['bandit_index']} | turno {item['turn']} | "
                f"vértice {item['vertex_id']} | {item['reason']}"
            )
        return lines

    in_analysis_screen = False
    show_final_graphs = False