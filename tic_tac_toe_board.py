import json
from dataclasses import dataclass, field, asdict
import redis

# Configure Redis client
tic_tac_toe_redis = redis.Redis(
    host='ai.thewcl.com',
    port=6379,
    password='atmega328',
    decode_responses=True
)

# Fixed Redis key for channel 6
GAME_STATE_KEY = "tic_tac_toe:game_state:6"

@dataclass
class TicTacToeBoard:
    state: str = "is_playing"
    player_turn: str = "x"
    positions: list[str] = field(default_factory=lambda: [""] * 9)

    def serialize(self) -> str:
        """Return the board as a JSON string."""
        return json.dumps(asdict(self))

    def save_to_redis(self) -> None:
        """Persist current board state to Redis."""
        board_data = asdict(self)
        tic_tac_toe_redis.json().set(GAME_STATE_KEY, ".", board_data)

    @classmethod
    def load_from_redis(cls) -> "TicTacToeBoard":
        """Load a board state from Redis for channel 6, initializing if missing."""
        data = tic_tac_toe_redis.json().get(GAME_STATE_KEY)
        if data is None:
            # Initialize a fresh board if none exists
            board = cls()
            board.save_to_redis()
            return board
        return cls(**data)

    def reset(self) -> None:
        """Reset board to its initial state and overwrite Redis."""
        self.state = "is_playing"
        self.player_turn = "x"
        self.positions = [""] * 9
        self.save_to_redis()

    def is_my_turn(self, i_am: str) -> bool:
        return self.player_turn == i_am

    def make_move(self, index: int) -> None:
        """Make a move at the given index, update state, and persist."""
        if self.state != "is_playing":
            print("Game is already over.")
            return
        if not (0 <= index < 9):
            print("Invalid index. Choose 0-8.")
            return
        if self.positions[index]:
            print("Spot taken, try again.")
            return

        # Place marker
        self.positions[index] = self.player_turn

        # Check for end conditions
        if self.check_winner():
            print(f"Player {self.player_turn.upper()} wins!")
            self.state = f"{self.player_turn}_won"
        elif self.check_draw():
            print("It's a draw!")
            self.state = "draw"
        else:
            self.switch_turn()

        # Persist after move
        self.save_to_redis()

    def check_winner(self) -> bool:
        wins = [
            (0,1,2),(3,4,5),(6,7,8),
            (0,3,6),(1,4,7),(2,5,8),
            (0,4,8),(2,4,6)
        ]
        for a, b, c in wins:
            if self.positions[a] == self.positions[b] == self.positions[c] != "":
                return True
        return False

    def check_draw(self) -> bool:
        return all(pos != "" for pos in self.positions) and not self.check_winner()

    def switch_turn(self) -> None:
        self.player_turn = "o" if self.player_turn == "x" else "x"

    def __str__(self) -> str:
        rows = []
        for i in range(0, 9, 3):
            row = [self.positions[j] if self.positions[j] else str(j) for j in range(i, i+3)]
            rows.append(" | ".join(row))
        return "\n---------\n".join(rows)
