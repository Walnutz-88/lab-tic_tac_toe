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

    def to_dict(self) -> dict:
        """Return a serializable dict of the current board state."""
        return asdict(self)

    def serialize(self) -> str:
        return json.dumps(self.to_dict())

    async def save_to_redis(self) -> None:
        """Persist current board state to Redis (async)."""
        await tic_tac_toe_redis.json().set(GAME_STATE_KEY, ".", self.to_dict())

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

    def make_move(self, player: str, index: int) -> dict:
        """
        Attempt to place `player` at `index`.
        Returns a dict:
          - success: bool
          - message: str
          - board: dict (only on success)
        """
        if self.state != "is_playing":
            return {"success": False, "message": "Game is already over."}
        if player != self.player_turn:
            return {
                "success": False,
                "message": f"It is not player {player.upper()}'s turn."
            }
        if not (0 <= index < 9):
            return {"success": False, "message": "Invalid index. Choose 0–8."}
        if self.positions[index] != "":
            return {"success": False, "message": "Spot taken, try again."}

        # apply move
        self.positions[index] = player

        # check for end conditions
        if self.check_winner():
            self.state = f"{player}_won"
            message = f"Player {player.upper()} wins!"
        elif self.check_draw():
            self.state = "draw"
            message = "It's a draw!"
        else:
            self.switch_turn()
            message = (
                f"Player {player.upper()} moved to {index}. "
                f"It is now {self.player_turn.upper()}'s turn."
            )

        return {"success": True, "message": message, "board": self.to_dict()}

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
            row = [
                self.positions[j] if self.positions[j] else str(j)
                for j in range(i, i+3)
            ]
            rows.append(" | ".join(row))
        return "\n---------\n".join(rows)
