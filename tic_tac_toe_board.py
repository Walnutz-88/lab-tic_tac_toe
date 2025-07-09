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


