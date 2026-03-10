from flask import Flask, render_template, request, jsonify
import chess
from ai import get_ai_move

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/new-game', methods=['POST'])
def new_game():
    board = chess.Board()
    return jsonify({
        'fen': board.fen(),
        'legal_moves': [m.uci() for m in board.legal_moves]
    })

@app.route('/api/legal-moves', methods=['POST'])
def legal_moves():
    data   = request.get_json()
    fen    = data.get('fen', chess.STARTING_FEN)
    square = data.get('square')
    board  = chess.Board(fen)
    sq     = chess.parse_square(square)
    moves  = [m.uci() for m in board.legal_moves if m.from_square == sq]
    return jsonify({'moves': moves})

@app.route('/api/move', methods=['POST'])
def make_move():
    data       = request.get_json()
    fen        = data.get('fen', chess.STARTING_FEN)
    uci_move   = data.get('move')
    difficulty = int(data.get('difficulty', 2))

    board = chess.Board(fen)

    try:
        move = chess.Move.from_uci(uci_move)
        if move not in board.legal_moves:
            return jsonify({'error': 'Illegal move'}), 400
        board.push(move)
    except Exception:
        return jsonify({'error': 'Invalid move'}), 400

    result      = _game_result(board)
    ai_move_uci = None

    if not board.is_game_over():
        ai_move = get_ai_move(board, depth=difficulty)
        if ai_move:
            ai_move_uci = ai_move.uci()
            board.push(ai_move)
            result = _game_result(board)

    return jsonify({
        'fen':         board.fen(),
        'ai_move':     ai_move_uci,
        'result':      result,
        'in_check':    board.is_check(),
        'legal_moves': [m.uci() for m in board.legal_moves]
    })

def _game_result(board):
    if not board.is_game_over():
        return None
    if board.is_checkmate():
        return 'white_wins' if board.turn == chess.BLACK else 'black_wins'
    return 'draw'

if __name__ == '__main__':
    app.run(debug=True, port=5000)
