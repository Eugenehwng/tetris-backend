from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum

class GameStatus(str, Enum):
    WAITING = "waiting"
    PLAYING = "playing"
    FINISHED = "finished"

class PlayerStatus(str, Enum):
    ALIVE = "alive"
    GAME_OVER = "game_over"
    DISCONNECTED = "disconnected"

class GameState(BaseModel):
    board: List[List[int]]
    score: int
    lines_cleared: int
    level: int
    current_piece: Optional[Dict[str, Any]] = None
    next_piece: Optional[Dict[str, Any]] = None
    held_piece: Optional[Dict[str, Any]] = None

class Player(BaseModel):
    id: str
    websocket: Optional[Any] = None  # WebSocket connection
    game_state: GameState
    status: PlayerStatus = PlayerStatus.ALIVE
    join_time: Optional[str] = None

class Room(BaseModel):
    id: str
    players: List[Player]
    status: GameStatus = GameStatus.WAITING
    max_players: int = 2
    created_at: Optional[str] = None

class GameMessage(BaseModel):
    type: str
    room_id: str
    player_id: str
    data: Optional[Dict[str, Any]] = None

class CreateRoomResponse(BaseModel):
    room_id: str
    message: str

class JoinRoomResponse(BaseModel):
    success: bool
    message: str
    player_id: Optional[str] = None
