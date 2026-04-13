from flask import Flask, render_template, jsonify, request
import sys
import os

# Adiciona a pasta src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from game import Game

app = Flask(__name__)
game = None


def init_game(rows, cols, distance, bandits):
    """Inicializa uma nova partida"""
    global game
    game = Game(distance, bandits, rows, cols)
    return game_to_json()


def game_to_json():
    """Converte o estado do jogo para JSON"""
    police_to_exit_path = game.get_police_to_exit_path()
    bandit_paths_to_exit = game.get_bandit_paths_to_exit()

    return {
        "grid": game.grid,
        "police_pos": list(game.police_pos),
        "exit_pos": list(game.exit_pos),
        "bandits": [list(b) for b in game.bandits],
        "turn": game.turn,
        "phase": game.phase,
        "message": game.message,
        "bandits_captured": game.bandits_captured,
        "bandits_reached_exit": game.bandits_reached_exit,
        "police_history": [list(p) for p in game.police_history],
        "bandit_history": [[list(p) for p in history] for history in game.bandit_history],
        "police_to_exit_path": police_to_exit_path,
        "bandit_paths_to_exit": bandit_paths_to_exit,
    }


@app.route('/')
def index():
    """Serve a página principal"""
    return render_template('index.html')


@app.route('/api/game/init', methods=['POST'])
def api_init_game():
    """Inicia uma nova partida"""
    data = request.json
    rows = data.get('rows', 12)
    cols = data.get('cols', 16)
    distance = data.get('distance', 3)
    bandits = data.get('bandits', 3)
    
    try:
        result = init_game(rows, cols, distance, bandits)
        return jsonify({"success": True, "game": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/api/game/move', methods=['POST'])
def api_move():
    """Move a polícia"""
    if game is None:
        return jsonify({"success": False, "error": "Jogo não inicializado"}), 400
    
    data = request.json
    dr = data.get('dr', 0)
    dc = data.get('dc', 0)
    
    old_bandits = [list(b) for b in game.bandits]
    success = game.move_police(dr, dc)
    new_bandits = [list(b) for b in game.bandits]
    
    return jsonify({
        "success": success,
        "game": game_to_json(),
        "old_bandits": old_bandits,
        "new_bandits": new_bandits,
    })


@app.route('/api/game/update-escape', methods=['POST'])
def api_update_escape():
    """Atualiza a fase de escape"""
    if game is None:
        return jsonify({"success": False, "error": "Jogo não inicializado"}), 400
    
    game.update_escape()
    
    return jsonify({
        "success": True,
        "game": game_to_json(),
    })


@app.route('/api/game/state', methods=['GET'])
def api_state():
    """Retorna o estado atual do jogo"""
    if game is None:
        return jsonify({"success": False, "error": "Jogo não inicializado"}), 400
    
    return jsonify({
        "success": True,
        "game": game_to_json(),
    })


@app.route('/api/game/final-report', methods=['GET'])
def api_final_report():
    """Retorna relatório final com caminhos e informações de Prim"""
    if game is None:
        return jsonify({"success": False, "error": "Jogo não inicializado"}), 400
    
    if game.phase != "done":
        return jsonify({"success": False, "error": "Jogo ainda não terminou"}), 400
    
    report = game.get_final_report()
    return jsonify({
        "success": True,
        "report": report,
    })


@app.route('/api/game/restart', methods=['POST'])
def api_restart():
    """Reinicia a partida"""
    if game is None:
        return jsonify({"success": False, "error": "Jogo não inicializado"}), 400
    
    game.restart()
    return jsonify({
        "success": True,
        "game": game_to_json(),
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)
