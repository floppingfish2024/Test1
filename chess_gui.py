import tkinter as tk
import chess
from chess_engine import ChessEngine
from learning import LearningAgent

class ChessGUI:
    def __init__(self, root):
        self.root = root
        self.engine = ChessEngine()
        self.agent = LearningAgent()
        self.agent.load_q_table("q_table.pkl")
        self.selected_square = None
        if self.root:
            self.root.title("Chess")
            self.model_var = tk.StringVar(self.root)
            self.model_menu = tk.OptionMenu(self.root, self.model_var, *self.get_models())
            self.model_menu.pack()
            self.model_var.trace("w", self.on_model_selected)
            self.canvas = tk.Canvas(self.root, width=400, height=400)
            self.canvas.pack()
            self.draw_board()
            self.canvas.bind("<Button-1>", self.on_square_clicked)

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

        if self.engine.get_board().move_stack:
            last_move = self.engine.get_board().peek()
            from_square = last_move.from_square
            to_square = last_move.to_square
            for square in [from_square, to_square]:
                col = chess.square_file(square)
                row = chess.square_rank(square)
                x1 = col * 50
                y1 = (7 - row) * 50
                x2 = x1 + 50
                y2 = y1 + 50
                self.canvas.create_rectangle(x1, y1, x2, y2, outline="yellow", width=2)

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
                self.highlight_legal_moves(square)
            else:
                move = chess.Move(self.selected_square, square)
                if self.engine.make_move(self.engine.get_board().san(move)):
                    self.draw_board()
                    self.root.after(100, self.agent_move)
                else:
                    self.draw_board() # Redraw to clear highlights
                self.selected_square = None

    def highlight_legal_moves(self, square):
        self.draw_board()
        for move in self.engine.get_board().legal_moves:
            if move.from_square == square:
                col = chess.square_file(move.to_square)
                row = chess.square_rank(move.to_square)
                x1 = col * 50
                y1 = (7 - row) * 50
                x2 = x1 + 50
                y2 = y1 + 50
                self.canvas.create_rectangle(x1, y1, x2, y2, outline="green", width=2)

    def agent_move(self):
        if not self.engine.get_board().is_game_over():
            move = self.agent.choose_action(self.engine.get_board())
            self.engine.make_move(move)
            self.draw_board()

    def get_models(self):
        import os
        files = [f for f in os.listdir('.') if os.path.isfile(f) and f.startswith("q_table_")]
        return files if files else ["No models found"]

    def on_model_selected(self, *args):
        model_name = self.model_var.get()
        if model_name != "No models found":
            self.agent.load_q_table(model_name)

def play_game(game_num, agent):
    print(f"Training game {game_num+1}")
    board = chess.Board()
    history = []
    while not board.is_game_over():
        state = board.fen()
        if board.turn == chess.WHITE:
            action = agent.choose_action(board)
        else:
            action = agent.choose_action(board)

        board.push_san(action)
        next_state = board.fen()
        reward = 0
        if board.is_checkmate():
            reward = 1 if board.turn == chess.BLACK else -1
        elif board.is_stalemate() or board.is_insufficient_material():
            reward = 0
        history.append((state, action, reward, board.copy()))
    return history

def train_bot(agent, num_games=1000):
    import multiprocessing
    pool = multiprocessing.Pool()
    results = pool.starmap(play_game, [(i, agent) for i in range(num_games)])
    pool.close()
    pool.join()
    for result in results:
        for state, action, reward, next_state in result:
            agent.learn(state, action, reward, next_state)
    agent.games_played += num_games
    agent.save_q_table(f"q_table_{agent.games_played}_games.pkl")
    print("Training complete.")


if __name__ == "__main__":
    import argparse
    import os
    import re
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", action="store_true")
    parser.add_argument("--games", type=int, default=1000)
    args = parser.parse_args()

    agent = LearningAgent()
    files = [f for f in os.listdir('.') if os.path.isfile(f) and f.startswith("q_table_")]
    if files:
        latest_file = max(files, key=lambda f: int(re.search(r'\d+', f).group()))
        agent.load_q_table(latest_file)

    if args.train:
        import sys
        train_bot(agent, args.games)
        sys.exit()
    else:
        root = tk.Tk()
        gui = ChessGUI(root)
        gui.agent = agent
        root.mainloop()
