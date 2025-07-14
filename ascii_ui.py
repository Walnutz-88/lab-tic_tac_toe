#!/usr/bin/env python3
import asyncio
import json
import os
import websockets

# WebSocket URL with your student number suffix
WEBSOCKET_URL = "ws://ai.thewcl.com:8706"

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def format_cell(idx, mark):
    """Return a string for one square: X, O, or its index."""
    if isinstance(mark, str) and mark.lower() in ('x', 'o'):
        return f' {mark.upper()} '
    return f' {idx} '


def render_board(positions):
    """Draw the board in ASCII based on a list of 9 positions."""
    clear_screen()
    rows = []
    for r in range(3):
        cells = [format_cell(r * 3 + i, positions[r * 3 + i]) for i in range(3)]
        rows.append('|'.join(cells))
    separator = "\n---+---+---\n"
    print(separator.join(rows))


async def listen_for_updates():
    """Connect to WebSocket and render board on each update."""
    async with websockets.connect(WEBSOCKET_URL) as ws:
        async for message in ws:
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                # Malformed JSON; skip
                continue
            positions = data.get('board').get('positions')
            if isinstance(positions, list) and len(positions) == 9:
                # Normalize empty strings to None
                normalized = [p if p else None for p in positions]
                render_board(normalized)


if __name__ == "__main__":
    try:
        asyncio.run(listen_for_updates())
    except KeyboardInterrupt:
        print("\nExiting...")
