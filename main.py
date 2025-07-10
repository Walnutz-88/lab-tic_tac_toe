from tic_tac_toe_board import TicTacToeBoard

def main():
    board = TicTacToeBoard.load_from_redis()
    print("Welcome to Tic-Tac-Toe!\n")

    while board.state == "is_playing":
        try:
            player = input("What player are you? (x or o): ")
            board = TicTacToeBoard.load_from_redis()
            if player == board.player_turn:
                print(board)
                choice = input(f"\nPlayer {board.player_turn.upper()}, enter move (0–8): ")
                idx = int(choice)
            else:
                print("It's not your turn.")
                continue
        except ValueError:
            print("Please enter a number 0–8.")
            continue

        board.make_move(idx)

    print("\nThanks for playing!")

if __name__ == "__main__":
    main()
