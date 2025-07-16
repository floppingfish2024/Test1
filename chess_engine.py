import chess

class ChessEngine:
    def __init__(self):
        self.board = chess.Board()

    def get_board(self):
        return self.board

    def make_move(self, move):
        try:
            self.board.push_san(move)
            return True
        except ValueError:
            return False

    def get_legal_moves(self):
        return [self.board.san(move) for move in self.board.legal_moves]
