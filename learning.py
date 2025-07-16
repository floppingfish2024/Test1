import chess
import random
import pickle

class LearningAgent:
    def __init__(self, alpha=0.1, gamma=0.9, epsilon=0.1):
        self.q_table = {}
        self.games_played = 0
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon

    def get_q_value(self, state, action):
        return self.q_table.get((state, action), 0.0)

    def choose_action(self, board):
        legal_moves = [board.san(move) for move in board.legal_moves]
        if random.uniform(0, 1) < self.epsilon:
            return random.choice(legal_moves)
        else:
            q_values = [self.get_q_value(board.fen(), move) for move in legal_moves]
            max_q = max(q_values)
            if q_values.count(max_q) > 1:
                best_moves = [i for i, x in enumerate(q_values) if x == max_q]
                i = random.choice(best_moves)
            else:
                i = q_values.index(max_q)
            return legal_moves[i]

    def learn(self, state, action, reward, next_state):
        old_q = self.get_q_value(state, action)
        next_legal_moves = [move for move in next_state.legal_moves]
        if not next_legal_moves:
            next_q = 0.0
        else:
            next_q_values = [self.get_q_value(next_state.fen(), next_state.san(move)) for move in next_legal_moves]
            next_q = max(next_q_values)
        new_q = old_q + self.alpha * (reward + self.gamma * next_q - old_q)
        self.q_table[(state, action)] = new_q

    def save_q_table(self, filename="q_table.pkl"):
        with open(filename, "wb") as f:
            pickle.dump({"q_table": self.q_table, "games_played": self.games_played}, f)

    def load_q_table(self, filename="q_table.pkl"):
        try:
            with open(filename, "rb") as f:
                data = pickle.load(f)
                if "q_table" in data:
                    self.q_table = data["q_table"]
                if "games_played" in data:
                    self.games_played = data["games_played"]
        except FileNotFoundError:
            self.q_table = {}
            self.games_played = 0
