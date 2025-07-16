import tkinter as tk
import chess
from chess_engine import ChessEngine
from learning import LearningAgent

class ChessGUI:
    def __init__(self, root):
        self.root = root
        if self.root:
            self.root.title("Chess")
            self.canvas = tk.Canvas(self.root, width=400, height=400)
            self.canvas.pack()
            self.draw_board()
            self.canvas.bind("<Button-1>", self.on_square_clicked)
            self.train_button = tk.Button(self.root, text="Train Bot", command=self.train_bot)
            self.train_button.pack()
        self.engine = ChessEngine()
        self.agent = LearningAgent()
        self.agent.load_q_table("q_table.pkl")
        self.selected_square = None

    def draw_board(self):
        self.canvas.delete("all")
        for row in range(8):
            for col in range(8):
                x1 = col * 50
                y1 = row * 50
                x2 = x1 + 50
                y2 = y1 + 50
                color = "white" if (row + col) % 2 == 0 else "gray"
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color)
        for square in range(64):
            piece = self.engine.get_board().piece_at(square)
            if piece:
                x = (square % 8) * 50 + 25
                y = (7 - (square // 8)) * 50 + 25
                self.canvas.create_text(x, y, text=piece.symbol(), font=("Arial", 24))

    def on_square_clicked(self, event):
        if self.engine.get_board().turn == chess.WHITE:
            col = event.x // 50
            row = 7 - (event.y // 50)
            square = chess.square(col, row)
            if self.selected_square is None:
                self.selected_square = square
            else:
                move = chess.Move(self.selected_square, square)
                if self.engine.make_move(self.engine.get_board().san(move)):
                    self.draw_board()
                    self.root.after(100, self.agent_move)
                self.selected_square = None

    def agent_move(self):
        if not self.engine.get_board().is_game_over():
            move = self.agent.choose_action(self.engine.get_board())
            self.engine.make_move(move)
            self.draw_board()

    def train_bot(self, num_games=1000):
        for i in range(num_games):
            print(f"Training game {i+1}/{num_games}")
            board = chess.Board()
            while not board.is_game_over():
                state = board.fen()
                if board.turn == chess.WHITE:
                    action = self.agent.choose_action(board)
                else:
                    action = self.agent.choose_action(board)

                board.push_san(action)
                next_state = board.fen()
                reward = 0
                if board.is_checkmate():
                    reward = 1 if board.turn == chess.BLACK else -1
                elif board.is_stalemate() or board.is_insufficient_material():
                    reward = 0
                self.agent.learn(state, action, reward, board)
        self.agent.save_q_table("q_table.pkl")
        print("Training complete.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", action="store_true")
    parser.add_argument("--games", type=int, default=1000)
    args = parser.parse_args()

    if args.train:
        gui = ChessGUI(None)
        gui.train_bot(args.games)
    else:
        root = tk.Tk()
        gui = ChessGUI(root)
        root.mainloop()
