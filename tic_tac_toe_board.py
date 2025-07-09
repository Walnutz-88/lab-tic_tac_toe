from dataclasses import dataclass, field
from typing import List

@dataclass
class TicTacToeBoard:
    state: str = "is_playing"
    player_turn: str = "x"
    positions: List[str] = field(default_factory=lambda: [""] * 9)
    
    def is_my_turn(self, i_am: str) -> bool:
        return self.player_turn == i_am

    def make_move(self, index: int) -> None:
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
        print(self) 


