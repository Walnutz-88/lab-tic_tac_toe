from fastapi import FastAPI, Body, HTTPException
from tic_tac_toe_board import TicTacToeBoard

app = FastAPI()

@app.get("/state")
async def get_state():
    board = await TicTacToeBoard.load_from_redis()
    return board.to_dict()

@app.post("/move")
async def post_move(player: str = Body(...), index: int = Body(...)):
    board = await TicTacToeBoard.load_from_redis()
    result = board.make_move(player, index)
    await board.save_to_redis()
    return {"result": result}

@app.post("/reset")
async def reset_board():
    board = TicTacToeBoard()
    board.reset()
    try:
        await board.save_to_redis()
        return {"message": "Board reset successful", "board": board.to_dict()}
    except HTTPException as e:
        # If Redis is unavailable, still return success with warning
        if e.status_code == 503:
            return {"message": "Board reset successful (warning: could not persist to Redis)", "board": board.to_dict()}
        raise
