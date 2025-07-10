#!/usr/bin/env python3
import argparse
import sys
from tic_tac_toe_board import TicTacToeBoard

def main():
    parser = argparse.ArgumentParser(description="Play or reset a Redis-backed Tic-Tac-Toe game")
    parser.add_argument(
        "--player",
        choices=["x", "o"],
        help="Which side you are playing: x or o (required unless using --reset)"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset the game board to an empty state and exit"
    )
    args = parser.parse_args()

    # Enforce that --player is required unless --reset was requested
    if not args.reset and args.player is None:
        parser.error("either --player PLAYER is required to play, or use --reset to wipe the board")

    # Handle reset-only mode
    if args.reset:
        board = TicTacToeBoard()   # fresh board in memory
        board.reset()              # writes empty board into Redis
        print("✔ Board has been reset. To start playing, run with --player x or --player o.")
        sys.exit(0)

    # --- normal play mode ---
    print("Welcome to Tic-Tac-Toe!\n")

    while True:
        board = TicTacToeBoard.load_from_redis()

        # If game ended, show final board and exit
        if board.state != "is_playing":
            print("\nGame over!")
            print(board)
            break

        # Not your turn? wait and refresh
        if args.player != board.player_turn:
            print(f"Waiting for player {board.player_turn.upper()} to move...")
            try:
                input("Press Enter to refresh... ")
            except KeyboardInterrupt:
                print("\nExiting.")
                sys.exit(0)
            continue

        # It's your turn
        print(board)
        move_str = input(f"\nPlayer {board.player_turn.upper()}, enter move (0–8): ")
        try:
            idx = int(move_str)
        except ValueError:
            print("⚠ Please enter a number between 0 and 8.")
            continue

        board.make_move(idx)
        # make_move() persists and flips turn (or ends the game) internally

    print("\nThanks for playing!")

if __name__ == "__main__":
    main()
