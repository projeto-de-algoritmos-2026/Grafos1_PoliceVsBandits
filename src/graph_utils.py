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