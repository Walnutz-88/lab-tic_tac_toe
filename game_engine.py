import argparse
import sys
import asyncio
import json

import httpx
import redis.asyncio as redis

# HTTP endpoint for our FastAPI server
API_BASE_URL = "http://localhost:8000"
# Redis pub/sub settings (only for update notifications)
REDIS_HOST = 'ai.thewcl.com'
REDIS_PORT = 6379
REDIS_PASSWORD = 'atmega328'
CHANNEL = 'ttt_game_state_changed'

async def handle_board_state(i_am_playing: str, client: httpx.AsyncClient) -> bool:
    """
    Fetch the current game state via HTTP and handle the player's turn.
    Returns True if a move was made, otherwise False.
    """
    try:
        resp = await client.get(f"{API_BASE_URL}/state")
        resp.raise_for_status()
    except httpx.ReadTimeout:
        print("⚠️ Request timed out when fetching game state. Retrying on next update...")
        return False
    except httpx.HTTPError as e:
        print(f"⚠️ HTTP error fetching state: {e}")
        return False

    board = resp.json()

    # If game already finished, display result and exit
    if board.get('state') != 'is_playing':
        print("\n🎮 Game Over 🎮")
        print(json.dumps(board, indent=2))
        if board['state'].endswith('_won'):
            print(f"\n🏆 Player {board['state'][0].upper()} wins!")
        else:
            print("\n🤝 It's a draw!")
        sys.exit(0)

    # If it's this player's turn, prompt and send move
    if board.get('player_turn') == i_am_playing:
        print(json.dumps(board, indent=2))
        move_str = input(f"\nPlayer {i_am_playing.upper()}, enter move (0–8): ")
        try:
            idx = int(move_str)
        except ValueError:
            print("Please enter a number between 0 and 8.")
            return False

        # Send move via HTTP POST
        try:
            move_resp = await client.post(
                f"{API_BASE_URL}/move",
                json={"player": i_am_playing, "index": idx},
            )
            move_resp.raise_for_status()
        except httpx.ReadTimeout:
            print("⚠️ Request timed out when sending move. Try again.")
            return False
        except httpx.HTTPError as e:
            print(f"⚠️ HTTP error sending move: {e}")
            return False

        result = move_resp.json().get('result', {})
        print(result.get('message', ''))

        if result.get('success'):
            # Fetch and display updated board
            try:
                updated_resp = await client.get(f"{API_BASE_URL}/state")
                updated_resp.raise_for_status()
                updated_board = updated_resp.json()
                print(json.dumps(updated_board, indent=2))
            except Exception:
                updated_board = board  # fallback

            # Publish update to channel so other clients wake up
            try:
                redis_pub = redis.Redis(
                    host=REDIS_HOST,
                    port=REDIS_PORT,
                    password=REDIS_PASSWORD,
                    decode_responses=True
                )
                payload = json.dumps({"by": i_am_playing, "board": updated_board})
                await redis_pub.publish(CHANNEL, payload)
            except Exception as e:
                print(f"⚠️ Warning: failed to publish update: {e}")

            return True
        return False

    # Not this player's turn
    print(f"⏳ Not your turn. It is {board.get('player_turn').upper()}'s turn. Waiting for updates...")
    return False

async def listen_for_updates(i_am_playing: str):
    """
    Subscribe to Redis pub/sub for state-change notifications,
    and invoke the HTTP-based handler initially and on each update.
    """
    # HTTP client for GET/POST with no read timeout
    async with httpx.AsyncClient(timeout=None) as client:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            decode_responses=True
        )
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(CHANNEL)
        print(f"Subscribed to '{CHANNEL}'. Waiting for updates…\n")

        # Initial check & prompt
        await handle_board_state(i_am_playing, client)

        # Listen for others' moves
        async for message in pubsub.listen():
            if message.get('type') == 'message':
                print("\n🔄 Detected a board update!")
                await handle_board_state(i_am_playing, client)

async def main():
    parser = argparse.ArgumentParser(
        description="Play or reset a Tic-Tac-Toe game via HTTP + Redis pub/sub"
    )
    parser.add_argument(
        "--player",
        choices=["x", "o"],
        help="Which side you are playing: x or o (required unless using --reset)"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset the game board via HTTP and exit"
    )
    args = parser.parse_args()

    if args.reset:
        async with httpx.AsyncClient(timeout=None) as client:
            try:
                resp = await client.post(f"{API_BASE_URL}/reset")
                resp.raise_for_status()
                data = resp.json()
                print(data.get('message', 'Board reset.'))
                print(json.dumps(data.get('board', {}), indent=2))
            except httpx.HTTPError as e:
                print(f"⚠️ HTTP error during reset: {e}")
        sys.exit(0)

    if not args.player:
        parser.error("either --player PLAYER is required to play, or use --reset to wipe the board")

    await listen_for_updates(args.player)

if __name__ == "__main__":
    asyncio.run(main())
