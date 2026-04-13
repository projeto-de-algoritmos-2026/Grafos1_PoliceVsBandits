// Estado do jogo
let gameState = null;
let isGameRunning = false;
let config = {
    rows: 12,
    cols: 16,
    distance: 3,
    bandits: 3,
};

// Canvas
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

// Configurações de desenho
const CELL_SIZE = 40;
const COLORS = {
    wall: '#34495e',
    empty: '#ecf0f1',
    police: '#ff6b6b',
    bandit: '#ffd93d',
    exit: '#45b7d1',
    path: '#95a5a6',
    grid: '#bdc3c7',
};

const MOVES = {
    up: { dr: -1, dc: 0 },
    down: { dr: 1, dc: 0 },
    left: { dr: 0, dc: -1 },
    right: { dr: 0, dc: 1 },
};

// Elementos DOM
const startBtn = document.getElementById('startBtn');
const restartBtn = document.getElementById('restartBtn');
const escapeStepBtn = document.getElementById('escapeStepBtn');
const finalReportBtn = document.getElementById('finalReportBtn');
const closeReportBtn = document.getElementById('closeReportBtn');
const backToGameBtn = document.getElementById('backToGameBtn');
const reportScreen = document.getElementById('reportScreen');
const moveBtns = document.querySelectorAll('.move-btn');
const setupSection = document.getElementById('setupSection');
const controlsSection = document.getElementById('controlsSection');

// Event Listeners
startBtn.addEventListener('click', startGame);
restartBtn.addEventListener('click', restartGame);
escapeStepBtn.addEventListener('click', stepEscape);
finalReportBtn.addEventListener('click', showFinalReport);
closeReportBtn.addEventListener('click', closeFinalReport);
backToGameBtn.addEventListener('click', closeFinalReport);
moveBtns.forEach(btn => btn.addEventListener('click', handleMoveButton));

// Teclado
document.addEventListener('keydown', handleKeyPress);

function handleKeyPress(e) {
    if (!isGameRunning) return;
    
    const keyMap = {
        'ArrowUp': 'up',
        'ArrowDown': 'down',
        'ArrowLeft': 'left',
        'ArrowRight': 'right',
        'w': 'up',
        's': 'down',
        'a': 'left',
        'd': 'right',
    };
    
    const move = keyMap[e.key];
    if (move) {
        e.preventDefault();
        movePolice(move);
    }
}

function handleMoveButton(e) {
    const move = e.target.closest('.move-btn').dataset.move;
    movePolice(move);
}

async function startGame() {
    config.rows = parseInt(document.getElementById('rowsInput').value);
    config.cols = parseInt(document.getElementById('colsInput').value);
    config.distance = parseInt(document.getElementById('distanceInput').value);
    config.bandits = parseInt(document.getElementById('banditsInput').value);
    
    try {
        const response = await fetch('/api/game/init', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config),
        });
        
        const data = await response.json();
        
        if (data.success) {
            gameState = data.game;
            isGameRunning = true;
            setupSection.style.display = 'none';
            controlsSection.style.display = 'block';
            escapeStepBtn.style.display = 'none';
            finalReportBtn.style.display = 'none';
            resizeCanvas();
            drawGame();
            updateUI();
        }
    } catch (err) {
        console.error('Erro ao iniciar jogo:', err);
        alert('Erro ao iniciar jogo');
    }
}

async function restartGame() {
    try {
        const response = await fetch('/api/game/restart', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            gameState = data.game;
            escapeStepBtn.style.display = 'none';
            finalReportBtn.style.display = 'none';
            drawGame();
            updateUI();
        }
    } catch (err) {
        console.error('Erro ao reiniciar:', err);
    }
}

async function movePolice(direction) {
    if (!isGameRunning || gameState.phase !== 'search') return;
    
    const move = MOVES[direction];
    if (!move) return;
    
    try {
        const response = await fetch('/api/game/move', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(move),
        });
        
        const data = await response.json();
        
        if (data.success) {
            gameState = data.game;
            drawGame();
            updateUI();
            
            if (gameState.phase === 'escape') {
                escapeStepBtn.style.display = 'block';
            }
        }
    } catch (err) {
        console.error('Erro ao mover:', err);
    }
}

async function stepEscape() {
    if (gameState.phase !== 'escape') return;
    
    try {
        const response = await fetch('/api/game/update-escape', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            gameState = data.game;
            drawGame();
            updateUI();
            
            if (gameState.phase === 'done') {
                escapeStepBtn.style.display = 'none';
                finalReportBtn.style.display = 'block';
            }
        }
    } catch (err) {
        console.error('Erro ao avançar escape:', err);
    }
}

async function showFinalReport() {
    try {
        const response = await fetch('/api/game/final-report');
        const data = await response.json();
        
        if (data.success) {
            const report = data.report;
            populateFinalReport(report);
            reportScreen.style.display = 'flex';
        }
    } catch (err) {
        console.error('Erro ao gerar relatório:', err);
    }
}

function closeFinalReport() {
    reportScreen.style.display = 'none';
}

function populateFinalReport(report) {
    const summary = report.summary;
    
    // Atualizar estatísticas
    document.getElementById('reportTurns').textContent = summary.turn;
    document.getElementById('reportCaptured').textContent = summary.bandits_captured;
    document.getElementById('reportEscaped').textContent = summary.bandits_reached_exit;
    document.getElementById('reportPoliceLen').textContent = summary.real_police_len;
    document.getElementById('reportOptimalLen').textContent = summary.initial_shortest_len;
    
    const efficiency = summary.initial_shortest_len > 0 
        ? ((summary.initial_shortest_len / summary.real_police_len) * 100).toFixed(1) 
        : 'N/A';
    document.getElementById('reportEfficiency').textContent = efficiency + '%';
    
    // Atualizar informações de Prim
    const prim = report.prim_graph;
    document.getElementById('primGrid').textContent = `${prim.rows}x${prim.cols}`;
    document.getElementById('primTotal').textContent = prim.total_cells;
    document.getElementById('primWalls').textContent = prim.wall_count;
    document.getElementById('primWallPercent').textContent = 
        ((prim.wall_count / prim.total_cells) * 100).toFixed(1);
    document.getElementById('primPaths').textContent = prim.path_count;
    document.getElementById('primPathPercent').textContent = 
        ((prim.path_count / prim.total_cells) * 100).toFixed(1);
    
    // Desenhar grafo de Prim
    drawPrimGraph(report.prim_graph);
    
    // Atualizar caminhos dos bandidos para a polícia
    const banditPathsContainer = document.getElementById('banditPathsContainer');
    banditPathsContainer.innerHTML = '';
    const banditPaths = report.bandit_paths_to_police || report.bandit_paths_to_exit || [];
    if (banditPaths.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'path-item';
        empty.textContent = 'Sem dados de caminho para exibir.';
        banditPathsContainer.appendChild(empty);
    }

    banditPaths.forEach(bp => {
        const pathStr = bp.path_ids.join(' → ');
        const item = document.createElement('div');
        item.className = 'path-item';
        item.innerHTML = `<strong>Bandido ${bp.bandit_idx + 1}</strong> 
                         (${bp.bandit_pos[0]}, ${bp.bandit_pos[1]})
                         <span class="distance">Dist: ${bp.distance || '∞'}</span><br>
                         Caminho: ${pathStr || 'Sem rota'}`;
        banditPathsContainer.appendChild(item);
    });
    
    // Atualizar caminho da polícia
    const policePath = report.police_path_to_exit;
    const policePathStr = policePath.path_ids.join(' → ') || 'Sem rota';
    document.getElementById('policePath').textContent = `Distância: ${policePath.distance}\n\n${policePathStr}`;
    
    // Atualizar log de movimentos
    const moveLogContainer = document.getElementById('moveLogContainer');
    moveLogContainer.innerHTML = '';
    report.move_log.forEach(move => {
        const pathStr = move.shortest_path_ids.join(' → ');
        const status = move.optimal ? '✓ Ótima' : '⚠ Desvio';
        const item = document.createElement('div');
        item.className = 'log-item';
        item.innerHTML = `${move.step}. ${move.from_id} → ${move.to_id} | ${status} | Dist: ${move.shortest_path_len}`;
        moveLogContainer.appendChild(item);
    });
    
    // Atualizar bandidos capturados
    if (report.captured_bandits_log.length > 0) {
        document.getElementById('capturedSection').style.display = 'block';
        const capturedContainer = document.getElementById('capturedLogContainer');
        capturedContainer.innerHTML = '';
        report.captured_bandits_log.forEach(captured => {
            const item = document.createElement('div');
            item.className = 'log-item';
            item.innerHTML = `Bandido ${captured.bandit_index} | Turno ${captured.turn} | ${captured.reason}`;
            capturedContainer.appendChild(item);
        });
    } else {
        document.getElementById('capturedSection').style.display = 'none';
    }
}

function drawPrimGraph(primGraph) {
    const primCanvas = document.getElementById('primCanvas');
    const primCtx = primCanvas.getContext('2d');
    
    const rows = primGraph.rows;
    const cols = primGraph.cols;
    const cellSize = Math.max(2, Math.min(20, 400 / cols));
    
    primCanvas.width = cols * cellSize;
    primCanvas.height = rows * cellSize;
    
    // Desenhar grid
    primCtx.fillStyle = '#ecf0f1';
    primCtx.fillRect(0, 0, primCanvas.width, primCanvas.height);
    
    // Desenhar células
    for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
            const cell = primGraph.grid[r][c];
            
            if (cell === 'X') {
                primCtx.fillStyle = '#34495e';
                primCtx.fillRect(c * cellSize, r * cellSize, cellSize, cellSize);
            } else if (cell === 'E') {
                primCtx.fillStyle = '#45b7d1';
                primCtx.fillRect(c * cellSize, r * cellSize, cellSize, cellSize);
            }
        }
    }
    
    // Desenhar grid lines
    primCtx.strokeStyle = '#bdc3c7';
    primCtx.lineWidth = 0.5;
    for (let r = 0; r <= rows; r++) {
        primCtx.beginPath();
        primCtx.moveTo(0, r * cellSize);
        primCtx.lineTo(primCanvas.width, r * cellSize);
        primCtx.stroke();
    }
    for (let c = 0; c <= cols; c++) {
        primCtx.beginPath();
        primCtx.moveTo(c * cellSize, 0);
        primCtx.lineTo(c * cellSize, primCanvas.height);
        primCtx.stroke();
    }
}

function resizeCanvas() {
    const width = config.cols * CELL_SIZE;
    const height = config.rows * CELL_SIZE;
    canvas.width = width;
    canvas.height = height;
}

function drawGame() {
    if (!gameState) return;
    
    // Limpar canvas
    ctx.fillStyle = COLORS.empty;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Desenhar grid
    drawGridBackground();
    
    // Desenhar parede e caminhos
    drawGrid();
    
    // Desenhar caminhos visualmente
    drawPathsVisually();
    
    // Desenhar bandidos
    gameState.bandits.forEach((bandit, idx) => {
        drawEntity(bandit[0], bandit[1], COLORS.bandit, '🦹');
    });
    
    // Desenhar polícia
    drawEntity(gameState.police_pos[0], gameState.police_pos[1], COLORS.police, '🚔');
    
    // Desenhar saída
    drawEntity(gameState.exit_pos[0], gameState.exit_pos[1], COLORS.exit, '🚪');
    
    // Desenhar grid lines
    drawGridLines();
}

function drawPathsVisually() {
    const pathToExit = (gameState.police_to_exit_path && gameState.police_to_exit_path.path) || [];
    ctx.strokeStyle = 'rgba(255, 193, 7, 0.5)';
    ctx.lineWidth = 3;
    ctx.setLineDash([5, 5]);
    
    if (pathToExit.length > 1) {
        ctx.beginPath();
        let firstPoint = true;
        for (const pos of pathToExit) {
            const x = pos[1] * CELL_SIZE + CELL_SIZE / 2;
            const y = pos[0] * CELL_SIZE + CELL_SIZE / 2;
            if (firstPoint) {
                ctx.moveTo(x, y);
                firstPoint = false;
            } else {
                ctx.lineTo(x, y);
            }
        }
        ctx.stroke();
    }
    
    ctx.setLineDash([]);

    // Caminhos dos bandidos até a saída (linhas sutis)
    if (gameState.bandit_paths_to_exit) {
        ctx.strokeStyle = 'rgba(69, 183, 209, 0.28)';
        ctx.lineWidth = 2;
        for (const banditPath of gameState.bandit_paths_to_exit) {
            const p = banditPath.path || [];
            if (p.length < 2) {
                continue;
            }
            ctx.beginPath();
            ctx.moveTo(p[0][1] * CELL_SIZE + CELL_SIZE / 2, p[0][0] * CELL_SIZE + CELL_SIZE / 2);
            for (let i = 1; i < p.length; i++) {
                ctx.lineTo(p[i][1] * CELL_SIZE + CELL_SIZE / 2, p[i][0] * CELL_SIZE + CELL_SIZE / 2);
            }
            ctx.stroke();
        }
    }
}

function drawGridBackground() {
    ctx.strokeStyle = COLORS.grid;
    ctx.lineWidth = 0.5;
    
    for (let r = 0; r <= config.rows; r++) {
        ctx.beginPath();
        ctx.moveTo(0, r * CELL_SIZE);
        ctx.lineTo(canvas.width, r * CELL_SIZE);
        ctx.stroke();
    }
    
    for (let c = 0; c <= config.cols; c++) {
        ctx.beginPath();
        ctx.moveTo(c * CELL_SIZE, 0);
        ctx.lineTo(c * CELL_SIZE, canvas.height);
        ctx.stroke();
    }
}

function drawGrid() {
    for (let r = 0; r < config.rows; r++) {
        for (let c = 0; c < config.cols; c++) {
            const cell = gameState.grid[r][c];
            
            if (cell === 'X') {
                ctx.fillStyle = COLORS.wall;
                ctx.fillRect(c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE);
            }
        }
    }
}

function drawGridLines() {
    ctx.strokeStyle = COLORS.grid;
    ctx.lineWidth = 0.5;
    
    for (let r = 0; r <= config.rows; r++) {
        ctx.beginPath();
        ctx.moveTo(0, r * CELL_SIZE);
        ctx.lineTo(canvas.width, r * CELL_SIZE);
        ctx.stroke();
    }
    
    for (let c = 0; c <= config.cols; c++) {
        ctx.beginPath();
        ctx.moveTo(c * CELL_SIZE, 0);
        ctx.lineTo(c * CELL_SIZE, canvas.height);
        ctx.stroke();
    }
}

function drawEntity(row, col, color, emoji) {
    const x = col * CELL_SIZE + CELL_SIZE / 2;
    const y = row * CELL_SIZE + CELL_SIZE / 2;
    
    // Desenhar círculo de fundo
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x, y, CELL_SIZE / 3, 0, Math.PI * 2);
    ctx.fill();
    
    // Desenhar emoji
    ctx.font = `${CELL_SIZE * 0.7}px Arial`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(emoji, x, y);
}

function updateUI() {
    if (!gameState) {
        return;
    }

    document.getElementById('turn').textContent = gameState.turn;
    document.getElementById('captured').textContent = gameState.bandits_captured;
    document.getElementById('escaped').textContent = gameState.bandits_reached_exit;
    document.getElementById('phase').textContent = gameState.phase;
    document.getElementById('message').textContent = gameState.message;

    // Mostrar menores caminhos atuais até a saída
    const policePath = gameState.police_to_exit_path;
    const policeDistance = policePath && policePath.distance !== null ? policePath.distance : 'sem rota';
    const policePathText = policePath && policePath.path_ids && policePath.path_ids.length > 0
        ? policePath.path_ids.join(' → ')
        : '-';
    document.getElementById('livePolicePath').textContent = `dist=${policeDistance} | ${policePathText}`;

    const liveBanditPaths = document.getElementById('liveBanditPaths');
    liveBanditPaths.innerHTML = '';
    if (gameState.bandit_paths_to_exit && gameState.bandit_paths_to_exit.length > 0) {
        gameState.bandit_paths_to_exit.forEach((bp) => {
            const row = document.createElement('p');
            const distance = bp.distance !== null ? bp.distance : 'sem rota';
            const pathText = bp.path_ids && bp.path_ids.length > 0 ? bp.path_ids.join(' → ') : '-';
            row.innerHTML = `<strong>Bandido ${bp.bandit_idx + 1}:</strong> dist=${distance} | ${pathText}`;
            liveBanditPaths.appendChild(row);
        });
    } else {
        const row = document.createElement('p');
        row.textContent = 'Sem bandidos no mapa.';
        liveBanditPaths.appendChild(row);
    }
    
    // Controlar exibição de botões conforme a fase
    if (gameState.phase === 'escape') {
        escapeStepBtn.style.display = 'block';
    } else if (gameState.phase === 'done') {
        escapeStepBtn.style.display = 'none';
        finalReportBtn.style.display = 'block';
    } else {
        escapeStepBtn.style.display = 'none';
        finalReportBtn.style.display = 'none';
    }
}

// Inicializar
document.addEventListener('DOMContentLoaded', () => {
    resizeCanvas();
    updateUI();
});
