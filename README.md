# Flask Chess AI

A web-based chess application built with Python and Flask. Play a classic game of chess against a computer AI powered by the Minimax algorithm with Alpha-Beta pruning.

## Features

-   **Interactive Chess Board**: A simple and clean UI to play chess in your browser.
-   **Player vs. AI**: Test your skills against a chess engine.
-   **Legal Move Highlighting**: Click on a piece to see all its valid moves.
-   **AI Opponent**: The AI uses the Minimax algorithm with Alpha-Beta pruning to determine the best move.
-   **Game State Detection**: Automatically detects check, checkmate, and stalemate conditions.
-   **Pawn Promotion**: Pawns are automatically promoted to a Queen upon reaching the opposite end of the board.

## Tech Stack

-   **Backend**: Python, Flask
-   **Frontend**: HTML, CSS, JavaScript (to interact with the Flask API)

## Getting Started

Follow these instructions to get a local copy up and running.

### Prerequisites

-   Python 3.x
-   `pip` (Python package installer)

### Installation & Setup

1.  **Clone the repository:**
    ```sh
    git clone [https://github.com/your-username/flask-chess-ai.git](https://github.com/your-username/flask-chess-ai.git)
    cd flask-chess-ai
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```sh
    # For Windows
    python -m venv venv
    .\venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the required packages:**
    The only dependency is Flask.
    ```sh
    pip install Flask
    ```

4.  **Run the application:**
    ```sh
    python app.py
    ```

5.  **Open your browser:**
    Navigate to `http://127.0.0.1:5000` to start playing.

## How to Play

1.  Open the application in your web browser.
2.  You will play as the White pieces.
3.  Click on one of your pieces to highlight its legal moves.
4.  Click on one of the highlighted green squares to move your piece.
5.  After your move, the AI (Black) will automatically make its move.
6.  The game ends when a checkmate or stalemate is reached. To start a new game, click the "New Game" button.

## Code Overview

The entire application logic is contained within `app.py`.

-   `ChessGame` **class**: This class encapsulates all the game logic.
    -   Board representation as a 2D list.
    -   Methods for finding pieces, calculating possible moves (`get_possible_moves`), and checking for game-ending conditions (`get_status`, `in_check`).
    -   `make_move()` to update the board state.

-   **AI Engine**:
    -   `evaluate()`: A simple evaluation function that scores the board based on the material value of the pieces.
    -   `minimax()`: The core recursive function that implements the Minimax algorithm with Alpha-Beta pruning to search the game tree for the optimal move.
    -   `get_best_move()`: A wrapper function that initiates the Minimax search for the current board state.

-   **Flask Routes**:
    -   `GET /`: Renders the main `index.html` page.
    -   `POST /new_game`: Resets the game state.
    -   `GET /get_state`: Returns the current JSON representation of the game.
    -   `POST /get_possible_moves`: Accepts a piece's position and returns its legal moves.
    -   `POST /move`: Accepts a player's move, validates it, updates the board, triggers the AI's move, and returns the new game state.

## Future Improvements

-   **Implement Castling and En Passant**: Add logic for these special chess moves.
-   **Adjustable AI Difficulty**: Allow the user to select the search depth for the Minimax algorithm.
-   **Player vs. Player Mode**: Add functionality for two human players.
-   **Move History**: Display a list of moves made throughout the game.
-   **UI Enhancements**: Improve the user interface and overall user experience.
