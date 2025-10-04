from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
import json
import uuid

# Create FastAPI app instance
app = FastAPI()

# Enable CORS so React frontend can communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React default port
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Store active WebSocket connections
# Key: room_id, Value: list of WebSocket connections in that room
active_rooms: Dict[str, List[WebSocket]] = {}

# Store game states for each room
# Key: room_id, Value: game state data
game_states: Dict[str, dict] = {}


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Tetris Backend Running"}


@app.post("/create-room")
async def create_room():
    """Create a new game room and return room ID"""
    room_id = str(uuid.uuid4())[:8]  # Generate short unique room ID
    active_rooms[room_id] = []  # Initialize empty player list
    game_states[room_id] = {
        "players": [],
        "status": "waiting"  # waiting, playing, finished
    }
    return {"room_id": room_id}


@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    """
    WebSocket endpoint for real-time game communication
    Each player connects to a room via this endpoint
    """
    # Accept the WebSocket connection
    await websocket.accept()
    
    # Add this connection to the room
    if room_id not in active_rooms:
        active_rooms[room_id] = []
    active_rooms[room_id].append(websocket)
    
    # Generate player ID
    player_id = str(uuid.uuid4())[:6]
    
    # Send player their ID
    await websocket.send_json({
        "type": "player_id",
        "player_id": player_id
    })
    
    # Notify all players in room about new player
    await broadcast_to_room(room_id, {
        "type": "player_joined",
        "player_id": player_id,
        "player_count": len(active_rooms[room_id])
    })
    
    try:
        # Listen for messages from this player
        while True:
            data = await websocket.receive_text()  # Receive message as text
            message = json.loads(data)  # Parse JSON
            
            # Handle different message types
            if message["type"] == "game_state":
                # Player sent their game state (board, score, etc.)
                # Broadcast to all other players in the room
                await broadcast_to_room(room_id, {
                    "type": "opponent_state",
                    "player_id": player_id,
                    "state": message["state"]
                }, exclude=websocket)
                
            elif message["type"] == "game_over":
                # Player's game ended
                await broadcast_to_room(room_id, {
                    "type": "player_game_over",
                    "player_id": player_id,
                    "score": message.get("score", 0)
                })
    
    except WebSocketDisconnect:
        # Player disconnected
        active_rooms[room_id].remove(websocket)
        
        # Notify remaining players
        await broadcast_to_room(room_id, {
            "type": "player_left",
            "player_id": player_id,
            "player_count": len(active_rooms[room_id])
        })
        
        # Clean up empty rooms
        if len(active_rooms[room_id]) == 0:
            del active_rooms[room_id]
            if room_id in game_states:
                del game_states[room_id]


async def broadcast_to_room(room_id: str, message: dict, exclude: WebSocket = None):
    """
    Send a message to all players in a room
    
    Args:
        room_id: The room to broadcast to
        message: Dictionary to send (will be converted to JSON)
        exclude: Optional WebSocket to exclude from broadcast
    """
    if room_id in active_rooms:
        for connection in active_rooms[room_id]:
            if connection != exclude:  # Don't send to excluded connection
                try:
                    await connection.send_json(message)
                except:
                    # Connection might be closed, skip it
                    pass


if __name__ == "__main__":
    import uvicorn
    # Run the server on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)