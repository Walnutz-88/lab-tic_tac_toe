import argparse
import sys
import asyncio
import json

from tic_tac_toe_board import (
    TicTacToeBoard,
    tic_tac_toe_redis,
    GAME_STATE_KEY,
    TTT_GAME_STATE_CHANGED
)

async def handle_board_state(i_am_playing: str) -> bool:
    """
    Load the board, and if it's this player's turn, prompt for a move,
    apply it, save state back to Redis, and publish on the pub/sub channel.
    Returns True if a move was made.
    """
    # fetch or init board
    data = await tic_tac_toe_redis.json().get(GAME_STATE_KEY)
    if data is None:
        board = TicTacToeBoard()
        await tic_tac_toe_redis.json().set(GAME_STATE_KEY, ".", json.loads(board.serialize()))
    else:
        board = TicTacToeBoard(**data)

    # if game already finished, exit
    if board.state != "is_playing":
        print(board)
        if board.state.endswith("_won"):
            winner = board.state[0].upper()
            print(f"\n🏁 Player {winner} has already won. Exiting.")
        else:
            print("\n🏁 The game ended in a draw. Exiting.")
        sys.exit(0)

    # only act if it's our turn
    if board.player_turn == i_am_playing:
        print(board)
        move_str = input(f"\nPlayer {board.player_turn.upper()}, enter move (0–8): ")
        try:
            idx = int(move_str)
        except ValueError:
            print("⚠ Please enter a number between 0 and 8.")
            return False

        board.make_move(idx)
        # persist updated board
        await tic_tac_toe_redis.json().set(GAME_STATE_KEY, ".", json.loads(board.serialize()))

        # publish update
        payload = json.dumps({"by": i_am_playing, "board": json.loads(board.serialize())})
        await tic_tac_toe_redis.publish(TTT_GAME_STATE_CHANGED, payload)
        return True

    return False


async def listen_for_updates(i_am_playing: str):
    """
    Subscribe to the game-state-changed channel and
    trigger handle_board_state() initially and on each update.
    """
    pubsub = tic_tac_toe_redis.pubsub()
    await pubsub.subscribe(TTT_GAME_STATE_CHANGED)
    print(f"🔔 Subscribed to '{TTT_GAME_STATE_CHANGED}'. Waiting for updates…\n")

    # initial check & prompt
    await handle_board_state(i_am_playing)

    # listen for others' moves
    async for message in pubsub.listen():
        if message.get("type") == "message":
            print("\n🔄 Detected a board update!")
            # run our handler again (will exit if finished)
            await handle_board_state(i_am_playing)


async def main():
    parser = argparse.ArgumentParser(
        description="Play or reset a Redis-backed Tic-Tac-Toe game (async)"
    )
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

    if args.reset:
        # async reset so we actually await the JSON.SET
        board = TicTacToeBoard()
        await board.reset()
        print("✔ Board has been reset. To start playing, run with --player x or --player o.")
        sys.exit(0)

    if args.player is None:
        parser.error("either --player PLAYER is required to play, or use --reset to wipe the board")

    # start the async pub/sub loop
    await listen_for_updates(args.player)


if __name__ == "__main__":
    asyncio.run(main())
