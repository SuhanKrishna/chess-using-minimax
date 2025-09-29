from flask import Flask, render_template, jsonify, request, session
import time
import copy
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

PIECES = {
    'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
    'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟',
    None: ' '
}

PIECE_VALUES = {
    'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000,
    'p': -100, 'n': -320, 'b': -330, 'r': -500, 'q': -900, 'k': -20000
}

def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8

class ChessGame:
    def __init__(self):
        self.reset_game()

    def reset_game(self):
        self.board = [
            ['r','n','b','q','k','b','n','r'],
            ['p','p','p','p','p','p','p','p'],
            [None]*8,
            [None]*8,
            [None]*8,
            [None]*8,
            ['P','P','P','P','P','P','P','P'],
            ['R','N','B','Q','K','B','N','R'],
        ]
        self.current_player = 'white'
        self.last_move = None
        self.game_over = False
        self.status = 'ongoing'
        self.winner = None
        self.ai_stats = {'nodes_evaluated': 0, 'nodes_pruned': 0, 'move_time': 0}

    @staticmethod
    def is_white_piece(p):
        return p is not None and p.isupper()

    @staticmethod
    def is_black_piece(p):
        return p is not None and p.islower()

    def find_king(self, is_white):
        target = 'K' if is_white else 'k'
        for r in range(8):
            for c in range(8):
                if self.board[r][c] == target:
                    return (r, c)
        return None

    def square_attacked(self, r, c, by_white):
        for rr in range(8):
            for cc in range(8):
                p = self.board[rr][cc]
                if not p:
                    continue
                if by_white and not self.is_white_piece(p):
                    continue
                if not by_white and not self.is_black_piece(p):
                    continue
                for (tr, tc) in self.get_possible_moves(rr, cc, attack_only=True):
                    if tr == r and tc == c:
                        return True
        return False

    def in_check(self, is_white):
        kpos = self.find_king(is_white)
        if not kpos:
            return True
        kr, kc = kpos
        return self.square_attacked(kr, kc, by_white=not is_white)

    def get_possible_moves(self, r, c, attack_only=False):
        piece = self.board[r][c]
        if not piece:
            return []
        moves = []
        is_white = self.is_white_piece(piece)
        p = piece.lower()

        if p == 'p':
            dir = -1 if is_white else 1
            start_row = 6 if is_white else 1
            for dc in (-1, 1):
                tr, tc = r + dir, c + dc
                if in_bounds(tr, tc):
                    target = self.board[tr][tc]
                    if target and ((is_white and self.is_black_piece(target)) or (not is_white and self.is_white_piece(target))):
                        moves.append((tr, tc))
                    elif attack_only:
                        moves.append((tr, tc))
            if not attack_only:
                tr, tc = r + dir, c
                if in_bounds(tr, tc) and self.board[tr][tc] is None:
                    moves.append((tr, tc))
                    tr2 = r + 2*dir
                    if r == start_row and in_bounds(tr2, c) and self.board[tr2][c] is None:
                        moves.append((tr2, c))

        elif p == 'n':
            jumps = [(2,1),(1,2),(-1,2),(-2,1),(-2,-1),(-1,-2),(1,-2),(2,-1)]
            for dr, dc in jumps:
                tr, tc = r + dr, c + dc
                if not in_bounds(tr, tc):
                    continue
                target = self.board[tr][tc]
                if target is None or (is_white and self.is_black_piece(target)) or ((not is_white) and self.is_white_piece(target)):
                    moves.append((tr, tc))

        elif p == 'b' or p == 'r' or p == 'q':
            directions = []
            if p in ('b', 'q'):
                directions += [(-1,-1),(-1,1),(1,-1),(1,1)]
            if p in ('r', 'q'):
                directions += [(-1,0),(1,0),(0,-1),(0,1)]
            for dr, dc in directions:
                tr, tc = r + dr, c + dc
                while in_bounds(tr, tc):
                    target = self.board[tr][tc]
                    if target is None:
                        moves.append((tr, tc))
                    else:
                        if (is_white and self.is_black_piece(target)) or ((not is_white) and self.is_white_piece(target)):
                            moves.append((tr, tc))
                        break
                    tr += dr
                    tc += dc

        elif p == 'k':
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    tr, tc = r + dr, c + dc
                    if not in_bounds(tr, tc):
                        continue
                    target = self.board[tr][tc]
                    if target is None or (is_white and self.is_black_piece(target)) or ((not is_white) and self.is_white_piece(target)):
                        moves.append((tr, tc))

        return moves

    def make_move(self, fr, fc, tr, tc):
        piece = self.board[fr][fc]
        self.board[fr][fc] = None
        if piece == 'P' and tr == 0:
            self.board[tr][tc] = 'Q'
        elif piece == 'p' and tr == 7:
            self.board[tr][tc] = 'q'
        else:
            self.board[tr][tc] = piece
        self.last_move = ((fr, fc), (tr, tc))

    def get_all_legal_moves(self, is_white_turn):
        legal = []
        original = copy.deepcopy(self.board)
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if not p:
                    continue
                if is_white_turn and not self.is_white_piece(p):
                    continue
                if not is_white_turn and not self.is_black_piece(p):
                    continue
                for (tr, tc) in self.get_possible_moves(r, c):
                    self.make_move(r, c, tr, tc)
                    if not self.in_check(is_white_turn):
                        legal.append({'from_row': r, 'from_col': c, 'to_row': tr, 'to_col': tc})
                    self.board = copy.deepcopy(original)
        return legal

    def evaluate(self):
        score = 0
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p:
                    score += PIECE_VALUES.get(p, 0)
        return score

    def get_status(self):
        is_white_turn = (self.current_player == 'white')
        legal = self.get_all_legal_moves(is_white_turn)
        if not legal:
            if self.in_check(is_white_turn):
                self.game_over = True
                self.status = 'checkmate'
                self.winner = 'black' if is_white_turn else 'white'
            else:
                self.game_over = True
                self.status = 'stalemate'
                self.winner = None
        else:
            self.game_over = False
            self.status = 'ongoing'
            self.winner = None
        return {'game_over': self.game_over, 'status': self.status, 'winner': self.winner}

    def minimax(self, depth, alpha, beta, maximizing_for_white):
        self.ai_stats['nodes_evaluated'] += 1
        status = self.get_status()
        if depth == 0 or status['game_over']:
            base = self.evaluate()
            if status['game_over']:
                if status['status'] == 'checkmate':
                    if status['winner'] == 'white':
                        base += 100000
                    elif status['winner'] == 'black':
                        base -= 100000
            return base, None

        is_white_turn = (self.current_player == 'white')
        legal = self.get_all_legal_moves(is_white_turn)
        if maximizing_for_white:
            best_val = -float('inf')
            best_move = None
            for mv in legal:
                board_backup = copy.deepcopy(self.board)
                prev_last = self.last_move
                prev_player = self.current_player

                self.make_move(mv['from_row'], mv['from_col'], mv['to_row'], mv['to_col'])
                self.current_player = 'black' if self.current_player == 'white' else 'white'

                val, _ = self.minimax(depth - 1, alpha, beta, not maximizing_for_white)

                self.board = board_backup
                self.last_move = prev_last
                self.current_player = prev_player

                if val > best_val:
                    best_val = val
                    best_move = mv
                alpha = max(alpha, val)
                if beta <= alpha:
                    self.ai_stats['nodes_pruned'] += 1
                    break
            return best_val, best_move
        else:
            best_val = float('inf')
            best_move = None
            for mv in legal:
                board_backup = copy.deepcopy(self.board)
                prev_last = self.last_move
                prev_player = self.current_player

                self.make_move(mv['from_row'], mv['from_col'], mv['to_row'], mv['to_col'])
                self.current_player = 'black' if self.current_player == 'white' else 'white'

                val, _ = self.minimax(depth - 1, alpha, beta, not maximizing_for_white)

                self.board = board_backup
                self.last_move = prev_last
                self.current_player = prev_player

                if val < best_val:
                    best_val = val
                    best_move = mv
                beta = min(beta, val)
                if beta <= alpha:
                    self.ai_stats['nodes_pruned'] += 1
                    break
            return best_val, best_move

    def get_best_move(self, depth=3):
        self.ai_stats = {'nodes_evaluated': 0, 'nodes_pruned': 0, 'move_time': 0}
        t0 = time.time()
        original_player = self.current_player
        maximizing_for_white = (self.current_player == 'white')
        _, move = self.minimax(depth, -float('inf'), float('inf'), maximizing_for_white)
        t1 = time.time()
        self.ai_stats['move_time'] = round((t1 - t0) * 1000)
        self.current_player = original_player
        return move

def game_to_dict(game: ChessGame):
    return {
        'board': game.board,
        'current_player': game.current_player,
        'last_move': game.last_move,
        'game_over': game.game_over,
        'status': game.status,
        'winner': game.winner,
        'ai_stats': game.ai_stats
    }

def game_from_dict(d: dict):
    g = ChessGame()
    g.board = d.get('board', g.board)
    g.current_player = d.get('current_player', g.current_player)
    g.last_move = d.get('last_move', g.last_move)
    g.game_over = d.get('game_over', g.game_over)
    g.status = d.get('status', g.status)
    g.winner = d.get('winner', g.winner)
    g.ai_stats = d.get('ai_stats', g.ai_stats)
    return g

def get_game_from_session():
    data = session.get('game')
    if data is None:
        g = ChessGame()
        session['game'] = game_to_dict(g)
        return g
    return game_from_dict(data)

def save_game_to_session(game: ChessGame):
    session['game'] = game_to_dict(game)
    session.modified = True

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/new_game", methods=["POST"])
def new_game():
    game = ChessGame()
    game.get_status()
    save_game_to_session(game)
    return jsonify(game_to_dict(game))

@app.route("/get_state", methods=["GET"])
def get_state():
    game = get_game_from_session()
    game.get_status()
    save_game_to_session(game)
    return jsonify(game_to_dict(game))

@app.route("/get_possible_moves", methods=["POST"])
def get_possible_moves_route():
    data = request.get_json(force=True)
    r, c = data['row'], data['col']
    game = get_game_from_session()
    piece = game.board[r][c]
    moves = []
    if piece and game.is_white_piece(piece) and game.current_player == 'white' and not game.game_over:
        original = copy.deepcopy(game.board)
        for (tr, tc) in game.get_possible_moves(r, c):
            game.make_move(r, c, tr, tc)
            if not game.in_check(True):
                moves.append([tr, tc])
            game.board = copy.deepcopy(original)
    return jsonify({'possible_moves': moves})

@app.route("/move", methods=["POST"])
def move():
    data = request.get_json(force=True)
    from_sq = data['from']
    to_sq = data['to']

    game = get_game_from_session()
    game.get_status()
    if game.game_over or game.current_player != 'white':
        save_game_to_session(game)
        return jsonify(game_to_dict(game))

    legal_white = game.get_all_legal_moves(True)
    cand = {'from_row': from_sq['row'], 'from_col': from_sq['col'], 'to_row': to_sq['row'], 'to_col': to_sq['col']}
    if cand not in legal_white:
        save_game_to_session(game)
        return jsonify(game_to_dict(game))

    game.make_move(cand['from_row'], cand['from_col'], cand['to_row'], cand['to_col'])
    game.current_player = 'black'
    game.get_status()
    if game.game_over:
        save_game_to_session(game)
        return jsonify(game_to_dict(game))
    ai_move = game.get_best_move(depth=3)
    if ai_move:
        game.make_move(ai_move['from_row'], ai_move['from_col'], ai_move['to_row'], ai_move['to_col'])
    game.current_player = 'white'
    game.get_status()

    save_game_to_session(game)
    return jsonify(game_to_dict(game))

if __name__ == "__main__":
    app.run(debug=True)
