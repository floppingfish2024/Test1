import chess

class ChessEngine:
    def __init__(self):
        self.board = chess.Board()

    def get_board(self):
        return self.board

    def make_move(self, move):
        if move in self.board.legal_moves:
            self.board.push(move)
            return True
        return False

    def get_legal_moves(self):
        return [self.board.san(move) for move in self.board.legal_moves]
