import random
from typing import List, Tuple, Dict, Any, Optional
from models import GameState, PlayerStatus

# Tetromino shapes with proper rotation matrices
TETROMINOS = {
    'I': {
        'shape': [[1, 1, 1, 1]],
        'color': '#00ffff',
        'rotations': [
            [[1, 1, 1, 1]],
            [[1], [1], [1], [1]]
        ]
    },
    'O': {
        'shape': [[1, 1], [1, 1]],
        'color': '#ffff00',
        'rotations': [
            [[1, 1], [1, 1]]
        ]
    },
    'T': {
        'shape': [[0, 1, 0], [1, 1, 1]],
        'color': '#800080',
        'rotations': [
            [[0, 1, 0], [1, 1, 1]],
            [[1, 0], [1, 1], [1, 0]],
            [[1, 1, 1], [0, 1, 0]],
            [[0, 1], [1, 1], [0, 1]]
        ]
    },
    'S': {
        'shape': [[0, 1, 1], [1, 1, 0]],
        'color': '#00ff00',
        'rotations': [
            [[0, 1, 1], [1, 1, 0]],
            [[1, 0], [1, 1], [0, 1]]
        ]
    },
    'Z': {
        'shape': [[1, 1, 0], [0, 1, 1]],
        'color': '#ff0000',
        'rotations': [
            [[1, 1, 0], [0, 1, 1]],
            [[0, 1], [1, 1], [1, 0]]
        ]
    },
    'J': {
        'shape': [[1, 0, 0], [1, 1, 1]],
        'color': '#0000ff',
        'rotations': [
            [[1, 0, 0], [1, 1, 1]],
            [[1, 1], [1, 0], [1, 0]],
            [[1, 1, 1], [0, 0, 1]],
            [[0, 1], [0, 1], [1, 1]]
        ]
    },
    'L': {
        'shape': [[0, 0, 1], [1, 1, 1]],
        'color': '#ffa500',
        'rotations': [
            [[0, 0, 1], [1, 1, 1]],
            [[1, 0], [1, 0], [1, 1]],
            [[1, 1, 1], [1, 0, 0]],
            [[1, 1], [0, 1], [0, 1]]
        ]
    }
}

BOARD_WIDTH = 10
BOARD_HEIGHT = 20

class TetrisGame:
    def __init__(self):
        self.board = [[0 for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.score = 0
        self.lines_cleared = 0
        self.level = 1
        self.current_piece = None
        self.next_piece = None
        self.held_piece = None
        self.piece_position = {'x': 0, 'y': 0}
        self.rotation = 0
        self.can_hold = True
        
        # Generate first pieces
        self.next_piece = self._generate_random_piece()
        self._spawn_new_piece()
    
    def _generate_random_piece(self) -> Dict[str, Any]:
        """Generate a random tetromino piece"""
        piece_type = random.choice(list(TETROMINOS.keys()))
        return {
            'type': piece_type,
            'shape': TETROMINOS[piece_type]['shape'],
            'color': TETROMINOS[piece_type]['color'],
            'rotations': TETROMINOS[piece_type]['rotations']
        }
    
    def _spawn_new_piece(self) -> bool:
        """Spawn a new piece at the top center. Returns False if game over"""
        self.current_piece = self.next_piece
        self.next_piece = self._generate_random_piece()
        self.rotation = 0
        self.can_hold = True
        
        # Position at top center
        piece_width = len(self.current_piece['shape'][0])
        self.piece_position = {
            'x': BOARD_WIDTH // 2 - piece_width // 2,
            'y': 0
        }
        
        # Check if game over
        if not self._is_valid_position():
            return False
        return True
    
    def _is_valid_position(self, piece=None, pos=None, rotation=None) -> bool:
        """Check if current piece position is valid"""
        if piece is None:
            piece = self.current_piece
        if pos is None:
            pos = self.piece_position
        if rotation is None:
            rotation = self.rotation
        
        shape = piece['rotations'][rotation % len(piece['rotations'])]
        
        for row in range(len(shape)):
            for col in range(len(shape[row])):
                if shape[row][col]:
                    new_x = pos['x'] + col
                    new_y = pos['y'] + row
                    
                    # Check boundaries
                    if new_x < 0 or new_x >= BOARD_WIDTH or new_y >= BOARD_HEIGHT:
                        return False
                    
                    # Check collision with existing pieces
                    if new_y >= 0 and self.board[new_y][new_x]:
                        return False
        
        return True
    
    def move_piece(self, dx: int, dy: int) -> bool:
        """Move piece by dx, dy. Returns True if successful"""
        new_pos = {
            'x': self.piece_position['x'] + dx,
            'y': self.piece_position['y'] + dy
        }
        
        if self._is_valid_position(pos=new_pos):
            self.piece_position = new_pos
            return True
        return False
    
    def rotate_piece(self) -> bool:
        """Rotate piece clockwise. Returns True if successful"""
        new_rotation = (self.rotation + 1) % len(self.current_piece['rotations'])
        
        if self._is_valid_position(rotation=new_rotation):
            self.rotation = new_rotation
            return True
        
        # Try wall kicks (move left/right if rotation hits wall)
        for kick_x in [-1, 1, -2, 2]:
            kick_pos = {
                'x': self.piece_position['x'] + kick_x,
                'y': self.piece_position['y']
            }
            if self._is_valid_position(pos=kick_pos, rotation=new_rotation):
                self.rotation = new_rotation
                self.piece_position = kick_pos
                return True
        
        return False
    
    def drop_piece(self) -> bool:
        """Drop piece one step down. Returns True if piece can still move"""
        return self.move_piece(0, 1)
    
    def hard_drop(self) -> int:
        """Drop piece to bottom instantly. Returns lines cleared"""
        drop_distance = 0
        while self.drop_piece():
            drop_distance += 1
        
        # Bonus points for hard drop
        self.score += drop_distance * 2
        return self._place_piece()
    
    def _place_piece(self) -> int:
        """Place current piece on board and clear lines. Returns lines cleared"""
        shape = self.current_piece['rotations'][self.rotation % len(self.current_piece['rotations'])]
        
        # Place piece on board
        for row in range(len(shape)):
            for col in range(len(shape[row])):
                if shape[row][col]:
                    board_y = self.piece_position['y'] + row
                    board_x = self.piece_position['x'] + col
                    if board_y >= 0:
                        self.board[board_y][board_x] = 1
        
        # Clear completed lines
        lines_cleared = self._clear_lines()
        
        # Update score and level
        if lines_cleared > 0:
            points = [0, 40, 100, 300, 1200][lines_cleared] * self.level
            self.score += points
            self.lines_cleared += lines_cleared
            self.level = self.lines_cleared // 10 + 1
        
        # Spawn new piece
        if not self._spawn_new_piece():
            return -1  # Game over
        
        return lines_cleared
    
    def _clear_lines(self) -> int:
        """Clear completed lines and return number of lines cleared"""
        lines_to_clear = []
        
        for row in range(BOARD_HEIGHT):
            if all(self.board[row]):
                lines_to_clear.append(row)
        
        # Remove lines from bottom up
        for row in sorted(lines_to_clear, reverse=True):
            del self.board[row]
            self.board.insert(0, [0 for _ in range(BOARD_WIDTH)])
        
        return len(lines_to_clear)
    
    def hold_piece(self) -> bool:
        """Hold current piece. Returns True if successful"""
        if not self.can_hold:
            return False
        
        if self.held_piece is None:
            self.held_piece = {
                'type': self.current_piece['type'],
                'shape': TETROMINOS[self.current_piece['type']]['shape'],
                'color': TETROMINOS[self.current_piece['type']]['color'],
                'rotations': TETROMINOS[self.current_piece['type']]['rotations']
            }
            self.current_piece = self.next_piece
            self.next_piece = self._generate_random_piece()
        else:
            # Swap current and held pieces
            self.current_piece, self.held_piece = self.held_piece, {
                'type': self.current_piece['type'],
                'shape': TETROMINOS[self.current_piece['type']]['shape'],
                'color': TETROMINOS[self.current_piece['type']]['color'],
                'rotations': TETROMINOS[self.current_piece['type']]['rotations']
            }
        
        self.rotation = 0
        self.can_hold = False
        
        # Reset position
        piece_width = len(self.current_piece['shape'][0])
        self.piece_position = {
            'x': BOARD_WIDTH // 2 - piece_width // 2,
            'y': 0
        }
        
        return True
    
    def get_ghost_position(self) -> Tuple[int, int]:
        """Get the position where the piece would land (ghost piece)"""
        ghost_y = self.piece_position['y']
        temp_pos = self.piece_position.copy()
        
        while True:
            temp_pos['y'] = ghost_y
            if not self._is_valid_position(pos=temp_pos):
                break
            ghost_y += 1
        
        return self.piece_position['x'], ghost_y - 1
    
    def get_game_state(self) -> GameState:
        """Get current game state"""
        return GameState(
            board=self.board,
            score=self.score,
            lines_cleared=self.lines_cleared,
            level=self.level,
            current_piece=self.current_piece,
            next_piece=self.next_piece,
            held_piece=self.held_piece
        )
    
    def get_drop_interval(self) -> int:
        """Get drop interval based on current level (in milliseconds)"""
        return max(50, 1000 - (self.level - 1) * 50)
