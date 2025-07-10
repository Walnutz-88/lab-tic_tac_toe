import json
from dataclasses import dataclass, field, asdict
import redis.asyncio as redis

# Configure async Redis client
tic_tac_toe_redis = redis.Redis(
    host='ai.thewcl.com',
    port=6379,
    password='atmega328',
    decode_responses=True
)

GAME_STATE_KEY = "tic_tac_toe:game_state:6"
TTT_GAME_STATE_CHANGED = "ttt_game_state_changed"

@dataclass
class TicTacToeBoard:
    state: str = "is_playing"
    player_turn: str = "x"
    positions: list[str] = field(default_factory=lambda: [""] * 9)

    def serialize(self) -> str:
        return json.dumps(asdict(self))

    async def save_to_redis(self) -> None:
        """Persist current board state to Redis (async)."""
        board_data = asdict(self)
        await tic_tac_toe_redis.json().set(GAME_STATE_KEY, ".", board_data)

    @classmethod
    async def load_from_redis(cls) -> "TicTacToeBoard":
        """Load or initialize a board state (async)."""
        data = await tic_tac_toe_redis.json().get(GAME_STATE_KEY)
        if data is None:
            board = cls()
            await board.save_to_redis()
            return board
        return cls(**data)

    async def reset(self) -> None:
        """Reset and persist the board state (async)."""
        self.state = "is_playing"
        self.player_turn = "x"
        self.positions = [""] * 9
        await self.save_to_redis()

    def is_my_turn(self, i_am: str) -> bool:
        return self.player_turn == i_am

    def make_move(self, index: int) -> None:
        # (same as before—this is sync logic, you can keep it here)
        if self.state != "is_playing":
            print("Game is already over.")
            return
        if not (0 <= index < 9):
            print("Invalid index. Choose 0-8.")
            return
        if self.positions[index]:
            print("Spot taken, try again.")
            return

        self.positions[index] = self.player_turn

        if self.check_winner():
            print(f"Player {self.player_turn.upper()} wins!")
            self.state = f"{self.player_turn}_won"
        elif self.check_draw():
            print("It's a draw!")
            self.state = "draw"
        else:
            self.switch_turn()

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
