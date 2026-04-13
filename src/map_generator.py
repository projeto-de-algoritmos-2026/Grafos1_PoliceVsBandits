import random
from graph_utils import shortest_path


def prims_maze_generator(rows, cols):
    """
    Gera um labirinto usando o algoritmo de Prim (Árvore Mínima Geradora).
    Cria um labirinto perfeito onde há exatamente um caminho entre dois pontos.
    
    Args:
        rows: número de linhas da grade
        cols: número de colunas da grade
    
    Returns:
        grid: 2D list representando o labirinto
    """
    # Inicializa a grade com paredes ("X")
    grid = [["X" for _ in range(cols)] for _ in range(rows)]
    
    # Começa com uma célula aleatória
    start_row = random.randint(0, rows - 1)
    start_col = random.randint(0, cols - 1)
    
    # Marca a célula inicial como caminho
    grid[start_row][start_col] = "."
    
    # Lista de paredes da árvore (frontier)
    walls = []
    
    # Adiciona as paredes adjacentes à célula inicial
    def add_walls(r, c):
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == "X":
                walls.append((nr, nc))
    
    add_walls(start_row, start_col)
    
    # Aplica Prim's algorithm
    while walls:
        # Escolhe uma parede aleatória
        wall_idx = random.randint(0, len(walls) - 1)
        wall_r, wall_c = walls.pop(wall_idx)
        
        # Conta quantas células abertas são vizinhas dessa parede
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        open_neighbors = 0
        
        for dr, dc in directions:
            nr, nc = wall_r + dr, wall_c + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == ".":
                open_neighbors += 1
        
        # Se a parede tem exatamente uma célula aberta adjacente, é uma parede da fronteira
        if open_neighbors == 1:
            # Marca essa parede como caminho
            grid[wall_r][wall_c] = "."
            add_walls(wall_r, wall_c)
    
    return grid


def random_free_cell(grid):
    """Retorna uma célula aleatória livre na grade."""
    free_cells = []

    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] == ".":
                free_cells.append((r, c))

    return random.choice(free_cells) if free_cells else None


def generate_valid_map(rows, cols, max_attempts=1000):
    """
    Gera um mapa válido para o jogo usando o algoritmo de Prim para criar o labirinto.
    Coloca a polícia e a saída em posições aleatórias com caminho garantido entre elas.
    """
    for attempt in range(max_attempts):
        # Gera o labirinto usando Prim's algorithm
        grid = prims_maze_generator(rows, cols)

        police = random_free_cell(grid)
        exit_pos = random_free_cell(grid)

        if police is None or exit_pos is None:
            continue

        if police == exit_pos:
            continue

        # Verifica se há caminho entre polícia e saída
        path, dist = shortest_path(grid, police, exit_pos)
        if not path or dist is None:
            continue

        grid[exit_pos[0]][exit_pos[1]] = "E"
        return grid, police, exit_pos

    raise RuntimeError("Não foi possível gerar um mapa válido.")