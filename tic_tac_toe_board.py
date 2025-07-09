from dataclasses import dataclass, field
from typing import List

@dataclass
class TicTacToeBoard:
    state: str = "is_playing"
    player_turn: str = "x"
    positions: List[str] = field(default_factory=lambda: [""] * 9)
    
    def is_my_turn(self, i_am: str) -> bool:
        return self.player_turn == i_am
