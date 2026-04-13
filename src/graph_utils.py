from collections import deque


def get_neighbors(grid, node):
    rows = len(grid)
    cols = len(grid[0])
    r, c = node

    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    neighbors = []

    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            if grid[nr][nc] != "X":
                neighbors.append((nr, nc))

    return neighbors


def bfs_distances(grid, start):
    queue = deque([start])
    distances = {start: 0}
    previous = {}

    while queue:
        current = queue.popleft()

        for neighbor in get_neighbors(grid, current):
            if neighbor not in distances:
                distances[neighbor] = distances[current] + 1
                previous[neighbor] = current
                queue.append(neighbor)

    return distances, previous


def shortest_path(grid, start, goal):
    distances, previous = bfs_distances(grid, start)

    if goal not in distances:
        return [], None

    path = []
    current = goal
    while current != start:
        path.append(current)
        current = previous[current]
    path.append(start)
    path.reverse()

    return path, distances[goal]


def prims_shortest_path(grid, start, goal):
    """
    Encontra o caminho mais curto usando Prim's algorithm (MST).
    Constrói uma árvore mínima geradora baseada no inicio e depois encontra caminho até o destino.
    
    Args:
        grid: 2D list do labirinto
        start: posição inicial (row, col)
        goal: posição destino (row, col)
    
    Returns:
        path: lista de posições do caminho
        distance: número de passos
    """
    rows = len(grid)
    cols = len(grid[0])
    
    if start == goal:
        return [start], 0

    # Inicializar MST com o nó inicial
    in_mst = {start}
    mst_edges = {}  # Mapeia nós da MST para seus pais
    frontier = []  # (peso, desempate, vizinho, pai)

    # Todas as arestas têm peso 1; desempate por id do vértice para estabilidade.
    def node_id(node):
        return node[0] * cols + node[1]

    for neighbor in get_neighbors(grid, start):
        if neighbor not in in_mst:
            frontier.append((1, node_id(neighbor), neighbor, start))

    while frontier:
        frontier.sort(key=lambda item: (item[0], item[1]))
        _, _, next_node, parent = frontier.pop(0)

        if next_node in in_mst:
            continue

        in_mst.add(next_node)
        mst_edges[next_node] = parent

        if next_node == goal:
            path = []
            current = goal
            while current != start:
                path.append(current)
                current = mst_edges[current]
            path.append(start)
            path.reverse()
            return path, len(path) - 1

        for neighbor in get_neighbors(grid, next_node):
            if neighbor not in in_mst:
                frontier.append((1, node_id(neighbor), neighbor, next_node))

    return [], None