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
                piece = self.engine.get_board().piece_at(self.selected_square)
                if piece is not None:
                    move = chess.Move(self.selected_square, square)
                    if piece.piece_type == chess.PAWN and chess.square_rank(square) == 7:
                        self.promote_pawn(move)
                    elif self.engine.make_move(move):
                        self.draw_board()
                        if not self.check_game_over():
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
        import logging
        logging.basicConfig(level=logging.INFO)
        if not self.engine.get_board().is_game_over():
            logging.info("Agent's turn")
            move_san = self.agent.choose_action(self.engine.get_board())
            logging.info(f"Agent chose move: {move_san}")
            try:
                move = self.engine.get_board().parse_san(move_san)
                logging.info(f"Parsed move: {move}")
                if self.engine.get_board().piece_at(move.from_square) is not None and self.engine.get_board().piece_at(move.from_square).piece_type == chess.PAWN and chess.square_rank(move.to_square) == 0:
                    move.promotion = chess.QUEEN
                    logging.info("Promoting pawn to Queen")
                self.engine.make_move(move)
                logging.info("Move made successfully")
            except ValueError:
                logging.error(f"Invalid move chosen by agent: {move_san}")
                # The agent chose an invalid move.
                # This can happen if the Q-table is not well-trained.
                # We'll just let the agent try again on the next turn.
                pass
            self.draw_board()
            self.check_game_over()

    def get_models(self):
        import os
        files = [f for f in os.listdir('.') if os.path.isfile(f) and f.startswith("q_table_")]
        return files if files else ["No models found"]

    def on_model_selected(self, *args):
        model_name = self.model_var.get()
        if model_name != "No models found":
            self.agent.load_q_table(model_name)

    def check_game_over(self):
        if self.engine.get_board().is_game_over():
            result = self.engine.get_board().result()
            if result == "1-0":
                message = "White wins!"
            elif result == "0-1":
                message = "Black wins!"
            else:
                message = "Draw!"

            self.show_message(message)
            self.engine.get_board().reset()
            self.draw_board()
            return True
        return False

    def show_message(self, message):
        dialog = tk.Toplevel(self.root)
        dialog.title("Game Over")
        tk.Label(dialog, text=message).pack()
        ok_button = tk.Button(dialog, text="OK", command=dialog.destroy)
        ok_button.pack()
        self.root.wait_window(dialog)

    def promote_pawn(self, move):
        promotion_piece = self.ask_promotion_piece()
        move.promotion = promotion_piece
        if self.engine.make_move(move):
            self.draw_board()
            self.root.after(100, self.agent_move)
        else:
            self.draw_board()

    def ask_promotion_piece(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Pawn Promotion")
        tk.Label(dialog, text="Promote to:").pack()

        piece_var = tk.IntVar()

        tk.Radiobutton(dialog, text="Queen", variable=piece_var, value=chess.QUEEN).pack()
        tk.Radiobutton(dialog, text="Rook", variable=piece_var, value=chess.ROOK).pack()
        tk.Radiobutton(dialog, text="Bishop", variable=piece_var, value=chess.BISHOP).pack()
        tk.Radiobutton(dialog, text="Knight", variable=piece_var, value=chess.KNIGHT).pack()

        ok_button = tk.Button(dialog, text="OK", command=dialog.destroy)
        ok_button.pack()

        self.root.wait_window(dialog)

        return piece_var.get()

def play_game(game_num, agent):
    board = chess.Board()
    history = []
    while not board.is_game_over():
        state = board.fen()
        if board.turn == chess.WHITE:
            action = agent.choose_action(board)
        else:
            action = agent.choose_action(board)

        move = board.parse_san(action)
        lost_piece = board.piece_at(move.from_square)
        captured_piece = board.piece_at(move.to_square)
        board.push_san(action)
        next_state = board.fen()
        reward = 0
        if captured_piece:
            if captured_piece.piece_type == chess.PAWN:
                reward = 1
            elif captured_piece.piece_type == chess.KNIGHT:
                reward = 3
            elif captured_piece.piece_type == chess.BISHOP:
                reward = 3
            elif captured_piece.piece_type == chess.ROOK:
                reward = 5
            elif captured_piece.piece_type == chess.QUEEN:
                reward = 9

        if board.is_capture(move) and lost_piece:
             if lost_piece.piece_type == chess.PAWN:
                reward = -1
             elif lost_piece.piece_type == chess.KNIGHT:
                reward = -3
             elif lost_piece.piece_type == chess.BISHOP:
                reward = -3
             elif lost_piece.piece_type == chess.ROOK:
                reward = -5
             elif lost_piece.piece_type == chess.QUEEN:
                reward = -9
        if board.is_checkmate():
            reward = 100 if board.turn == chess.BLACK else -100
        elif board.is_stalemate() or board.is_insufficient_material():
            reward = 0
        history.append((state, action, reward, board.copy()))

    result = board.result()
    moves = board.fullmove_number
    return history, result, moves

def train_bot(agent, num_games=1000):
    import multiprocessing
    import numpy as np

    wins = 0
    losses = 0
    draws = 0
    total_moves = 0

    for i in range(num_games):
        history, result, moves = play_game(i, agent)
        for state, action, reward, next_state in history:
            agent.learn(state, action, reward, next_state)
        if result == "1-0":
            wins += 1
        elif result == "0-1":
            losses += 1
        else:
            draws += 1
        total_moves += moves

        if (i + 1) % 100 == 0:
            print(f"Games played: {i + 1}/{num_games}")

    agent.games_played += num_games
    agent.save_q_table(f"q_table_{agent.games_played}_games.pkl")

    print("Training complete.")
    print(f"Games played: {num_games}")
    print(f"Wins: {wins} ({wins/num_games*100:.2f}%)")
    print(f"Losses: {losses} ({losses/num_games*100:.2f}%)")
    print(f"Draws: {draws} ({draws/num_games*100:.2f}%)")
    print(f"Average moves per game: {total_moves/num_games:.2f}")

    q_values = [v for k, v in agent.q_table.items()]
    if q_values:
        print(f"Average Q-value: {np.mean(q_values):.4f}")
    else:
        print("Q-table is empty, no Q-values to average.")


def compare_bots(model1_file, model2_file, num_games=100):
    agent1 = LearningAgent()
    agent1.load_q_table(model1_file)
    agent1.epsilon = 0 # No exploration
    agent2 = LearningAgent()
    agent2.load_q_table(model2_file)
    agent2.epsilon = 0 # No exploration

    model1_wins = 0
    model2_wins = 0
    draws = 0

    for i in range(num_games):
        board = chess.Board()
        while not board.is_game_over():
            if board.turn == chess.WHITE:
                action = agent1.choose_action(board)
            else:
                action = agent2.choose_action(board)
            board.push_san(action)

        result = board.result()
        if result == "1-0":
            model1_wins += 1
        elif result == "0-1":
            model2_wins += 1
        else:
            draws += 1

        if (i + 1) % 10 == 0:
            print(f"Games played: {i + 1}/{num_games}")

    print("Comparison complete.")
    print(f"Model 1 ({model1_file}) wins: {model1_wins} ({model1_wins/num_games*100:.2f}%)")
    print(f"Model 2 ({model2_file}) wins: {model2_wins} ({model2_wins/num_games*100:.2f}%)")
    print(f"Draws: {draws} ({draws/num_games*100:.2f}%)")

if __name__ == "__main__":
    import argparse
    import os
    import re
    import sys
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", action="store_true")
    parser.add_argument("--games", type=int, default=1000)
    parser.add_argument("--compare", nargs=2, help="Compare two models")
    args = parser.parse_args()

    if args.compare:
        compare_bots(args.compare[0], args.compare[1], args.games)
        sys.exit()

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
