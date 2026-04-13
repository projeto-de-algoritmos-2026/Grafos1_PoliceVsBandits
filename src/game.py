import random
from graph_utils import bfs_distances, shortest_path, get_neighbors, prims_shortest_path
from map_generator import generate_valid_map


class Game:
    def __init__(self, distance_value, num_bandits, rows, cols):
        self.distance_value = distance_value
        self.num_bandits = num_bandits
        self.rows = rows
        self.cols = cols

        self.turn = 0
        self.phase = "search"   # search | escape | done
        self.message = ""
        self.bandit_paths = []
        self.valid_ring_positions = []
        self.bandits_reached_exit = 0
        self.bandits_captured = 0

        self.final_police_path = []
        self.final_bandit_paths = []
        self.show_final_graphs = False
        self.in_analysis_screen = False

        self.police_history = []
        self.bandit_history = []
        self.move_log = []
        self.captured_bandits_log = []

        self.initial_shortest_path = []
        self.initial_police_to_exit_path = {"path": [], "distance": None, "path_ids": []}
        self.initial_bandit_paths_to_police = []

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

        self.final_police_path = []
        self.final_bandit_paths = []
        self.show_final_graphs = False
        self.in_analysis_screen = False

        self.bandits = self.spawn_bandits()
        self.update_valid_ring()

        self.police_history = [self.police_pos]
        self.bandit_history = [[b] for b in self.bandits]
        self.move_log = []
        self.captured_bandits_log = []

        path, _ = shortest_path(self.grid, self.police_pos, self.exit_pos)
        self.initial_shortest_path = path[:] if path else []
        self.initial_police_to_exit_path = self.get_police_to_exit_path()
        self.initial_bandit_paths_to_police = self.get_bandit_to_police_paths()

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
        candidates = []
        for r in range(self.rows):
            for c in range(self.cols):
                pos = (r, c)
                if self.grid[r][c] == "." and pos != self.police_pos and pos != self.exit_pos:
                    candidates.append(pos)

        # fallback para mapas muito pequenos
        if not candidates:
            self.update_valid_ring()
            candidates = self.valid_ring_positions[:]

        random.shuffle(candidates)
        return candidates[: self.num_bandits]

    def _candidate_bandit_moves(self, bandit_pos):
        candidates = [bandit_pos]
        for neighbor in get_neighbors(self.grid, bandit_pos):
            candidates.append(neighbor)

        unique = []
        seen = set()
        for pos in candidates:
            if pos not in seen:
                unique.append(pos)
                seen.add(pos)
        return unique

    def _distance_to_exit_with_prim(self, pos):
        path, dist = prims_shortest_path(self.grid, pos, self.exit_pos)
        if not path or dist is None:
            return None
        return dist

    def _capture_bandits_on_police(self):
        survivors = []
        survivor_history = []
        captured_now = 0

        for i, bandit in enumerate(self.bandits):
            history = self.bandit_history[i]
            if bandit == self.police_pos:
                captured_now += 1
                self.captured_bandits_log.append({
                    "bandit_index": i + 1,
                    "turn": self.turn,
                    "vertex_id": self.pos_to_id(bandit),
                    "position": bandit,
                    "reason": "capturado pela polícia",
                })
                continue

            survivors.append(bandit)
            survivor_history.append(history)

        self.bandits = survivors
        self.bandit_history = survivor_history
        self.bandits_captured += captured_now
        return captured_now

    def reposition_bandits(self):
        distances_from_police, _ = bfs_distances(self.grid, self.police_pos)

        new_bandits = []
        new_histories = []

        current_bandits = self.bandits[:]
        current_histories = self.bandit_history[:]

        occupied = set()
        escaped_now = 0

        for i, bandit in enumerate(current_bandits):
            history = current_histories[i][:]

            local_moves = self._candidate_bandit_moves(bandit)

            valid_local_moves = [pos for pos in local_moves if pos not in occupied]

            safe_moves = []
            fallback_moves = []
            for pos in valid_local_moves:
                d_exit = self._distance_to_exit_with_prim(pos)
                d_police = distances_from_police.get(pos, None)
                if d_exit is None or d_police is None:
                    continue

                candidate = (d_exit, -d_police, self.pos_to_id(pos), pos)
                if d_police >= self.distance_value:
                    safe_moves.append(candidate)
                else:
                    fallback_moves.append(candidate)

            if safe_moves:
                safe_moves.sort(key=lambda item: (item[0], item[1], item[2]))
                best = safe_moves[0][3]
            elif fallback_moves:
                # Sem opção segura: tenta maximizar distância da polícia.
                fallback_moves.sort(key=lambda item: (item[1], item[0], item[2]))
                best = fallback_moves[0][3]
            else:
                # Sem rota para saída, fica parado se possível.
                best = bandit

            history.append(best)

            if best == self.police_pos:
                self.bandits_captured += 1
                self.captured_bandits_log.append({
                    "bandit_index": i + 1,
                    "turn": self.turn,
                    "vertex_id": self.pos_to_id(best),
                    "position": best,
                    "reason": "interceptado ao tentar fugir",
                })
                continue

            if best == self.exit_pos:
                escaped_now += 1
                self.bandits_reached_exit += 1
                continue

            occupied.add(best)
            new_bandits.append(best)
            new_histories.append(history)

        self.bandits = new_bandits
        self.bandit_history = new_histories
        return escaped_now

    def get_bandit_paths_to_exit(self):
        paths = []
        for i, bandit in enumerate(self.bandits):
            path, dist = shortest_path(self.grid, bandit, self.exit_pos)
            paths.append({
                "bandit_idx": i,
                "bandit_pos": list(bandit),
                "path": [list(p) for p in path] if path else [],
                "distance": dist,
                "path_ids": self.path_to_ids(path) if path else [],
            })
        return paths

    def register_move_log(self, old_pos, new_pos):
        shortest_now, _ = shortest_path(self.grid, new_pos, self.exit_pos)

        old_shortest, _ = shortest_path(self.grid, old_pos, self.exit_pos)
        if old_shortest and len(old_shortest) >= 2:
            optimal_move = (old_shortest[1] == new_pos)
        else:
            optimal_move = False

        self.move_log.append({
            "step": len(self.move_log) + 1,
            "from_pos": old_pos,
            "to_pos": new_pos,
            "from_id": self.pos_to_id(old_pos),
            "to_id": self.pos_to_id(new_pos),
            "shortest_path_positions": shortest_now[:] if shortest_now else [],
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

        captured_on_contact = self._capture_bandits_on_police()
        escaped_now = self.reposition_bandits()
        captured_after_move = self._capture_bandits_on_police()

        if not self.bandits:
            self.phase = "done"
            self.message = (
                f"Fim da simulação. {self.bandits_reached_exit} bandido(s) fugiram e "
                f"{self.bandits_captured} foram capturados."
            )
            return True

        police_exit_path = self.get_police_path()
        remaining = len(police_exit_path) - 1 if police_exit_path else "sem rota"
        self.message = (
            f"Turno {self.turn}. Distância polícia→saída: {remaining}. "
            f"Fugiram neste turno: {escaped_now}. "
            f"Capturados neste turno: {captured_on_contact + captured_after_move}."
        )
        return True

    def start_escape_phase(self):
        self.phase = "escape"
        self.message = "Saída encontrada. Os bandidos restantes estão fugindo automaticamente."

        self.bandit_paths = []
        survivors = []
        survivor_history = []

        for i, bandit in enumerate(self.bandits):
            path, dist = prims_shortest_path(self.grid, bandit, self.exit_pos)
            if path and dist is not None:
                self.bandit_paths.append(path[:])
                survivors.append(bandit)
                survivor_history.append(self.bandit_history[i])
            else:
                self.bandits_captured += 1
                self.captured_bandits_log.append({
                    "bandit_index": i + 1,
                    "turn": self.turn,
                    "vertex_id": self.pos_to_id(bandit),
                    "position": bandit,
                    "reason": "sem rota até a saída na fase final",
                })

        self.bandits = survivors
        self.bandit_history = survivor_history

        if not self.bandits:
            self.phase = "done"
            self.message = (
                "Fim da simulação. Nenhum bandido restante conseguiu rota até a saída. "
                "Clique em 'Gerar grafos finais'."
            )

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
            self.message = (
                f"Fim da simulação. {self.bandits_reached_exit} bandido(s) chegaram à saída e "
                f"{self.bandits_captured} foram presos. Clique em 'Gerar grafos finais'."
            )
        else:
            self.message = (
                f"Fase final em andamento. "
                f"{self.bandits_reached_exit} bandido(s) já chegaram à saída."
            )
        return True

    def generate_final_graphs(self):
        if self.phase != "done":
            return

        self.show_final_graphs = True
        self.final_police_path = self.police_history[:]
        self.final_bandit_paths = [history[:] for history in self.bandit_history]
        self.in_analysis_screen = True
        self.message = "Tela final de análise gerada."

    def exit_analysis_screen(self):
        self.in_analysis_screen = False

    def get_current_distances_to_police(self):
        distances, _ = bfs_distances(self.grid, self.police_pos)
        result = []

        for bandit in self.bandits:
            result.append(distances.get(bandit, None))

        return result

    def get_summary(self):
        police_path = self.get_police_path()
        remaining = None if not police_path else len(police_path) - 1

        return {
            "turn": self.turn,
            "phase": self.phase,
            "distance_value": self.distance_value,
            "bandits_on_map": len(self.bandits),
            "bandits_reached_exit": self.bandits_reached_exit,
            "bandits_captured": self.bandits_captured,
            "remaining_path": remaining,
            "show_final_graphs": self.show_final_graphs,
            "in_analysis_screen": self.in_analysis_screen,
            "real_police_len": max(0, len(self.police_history) - 1),
            "initial_shortest_len": max(0, len(self.initial_shortest_path) - 1),
            "rows": self.rows,
            "cols": self.cols,
        }

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

    def get_bandit_to_police_paths(self):
        """Calcula caminhos mais curtos de cada bandido até a polícia"""
        paths = []
        distances, _ = bfs_distances(self.grid, self.police_pos)
        
        for i, bandit in enumerate(self.bandits):
            path, dist = shortest_path(self.grid, bandit, self.police_pos)
            paths.append({
                "bandit_idx": i,
                "bandit_pos": list(bandit),
                "path": [list(p) for p in path] if path else [],
                "distance": dist,
                "path_ids": self.path_to_ids(path) if path else [],
            })
        return paths

    def get_police_to_exit_path(self):
        """Retorna caminho mais curto da polícia até a saída"""
        path, dist = shortest_path(self.grid, self.police_pos, self.exit_pos)
        return {
            "path": [list(p) for p in path] if path else [],
            "distance": dist,
            "path_ids": self.path_to_ids(path) if path else [],
        }

    def get_prim_graph_info(self):
        """Retorna informações do grafo gerado por Prim para visualização"""
        return {
            "rows": self.rows,
            "cols": self.cols,
            "grid": self.grid,
            "total_cells": self.rows * self.cols,
            "wall_count": sum(row.count("X") for row in self.grid),
            "path_count": sum(1 for r in self.grid for c in r if c != "X"),
        }

    def get_final_report(self):
        """Gera relatório final completo"""
        bandit_paths_to_exit = self.get_bandit_paths_to_exit()
        bandit_paths_to_police = self.initial_bandit_paths_to_police[:]
        police_exit_path = self.initial_police_to_exit_path
        prim_info = self.get_prim_graph_info()
        
        return {
            "summary": self.get_summary(),
            "bandit_paths_to_exit": bandit_paths_to_exit,
            "bandit_paths_to_police": bandit_paths_to_police,
            "police_path_to_exit": police_exit_path,
            "prim_graph": prim_info,
            "move_log": self.move_log,
            "captured_bandits_log": self.captured_bandits_log,
            "police_history": [list(p) for p in self.police_history],
            "bandit_history": [[list(p) for p in history] for history in self.bandit_history],
        }