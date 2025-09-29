document.addEventListener('DOMContentLoaded', () => {
  const boardElement = document.getElementById('chess-board');
  const statusText = document.getElementById('status-text');
  const lastMoveText = document.getElementById('last-move-text');
  const nodesEvaluatedEl = document.getElementById('nodes-evaluated');
  const nodesPrunedEl = document.getElementById('nodes-pruned');
  const moveTimeEl = document.getElementById('move-time');
  const newGameBtn = document.getElementById('new-game-btn');

  const PIECES = {
    'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
    'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
  };

  let selectedSquare = null;
  let possibleMoves = [];
  let gameOver = false;

  function clearHighlights() {
    document.querySelectorAll('.chess-square').forEach(sq => {
      sq.classList.remove('selected', 'possible-move', 'capture-move', 'last-move');
    });
  }

  function highlightPossibleMoves() {
    possibleMoves.forEach(([r, c]) => {
      const sq = document.querySelector(`.chess-square[data-row='${r}'][data-col='${c}']`);
      if (!sq) return;
      // will mark as capture if contains a black piece glyph
      const hasPiece = sq.querySelector('.piece');
      if (hasPiece) {
        sq.classList.add('capture-move');
      } else {
        sq.classList.add('possible-move');
      }
    });
  }

  function renderBoard(board, lastMove) {
    boardElement.innerHTML = '';
    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        const square = document.createElement('div');
        square.classList.add('chess-square');
        square.classList.add((r + c) % 2 === 0 ? 'light-square' : 'dark-square');
        square.dataset.row = r;
        square.dataset.col = c;

        const p = board[r][c];
        if (p) {
          const span = document.createElement('span');
          span.classList.add('piece');
          span.classList.add(p === p.toUpperCase() ? 'white' : 'black');
          span.textContent = PIECES[p] || '';
          square.appendChild(span);
        }

        square.addEventListener('click', () => onSquareClick(r, c));
        boardElement.appendChild(square);
      }
    }

    // Highlight last move
    if (lastMove) {
      const [[fr, fc], [tr, tc]] = lastMove;
      const fromSq = document.querySelector(`.chess-square[data-row='${fr}'][data-col='${fc}']`);
      const toSq = document.querySelector(`.chess-square[data-row='${tr}'][data-col='${tc}']`);
      if (fromSq) fromSq.classList.add('last-move');
      if (toSq) toSq.classList.add('last-move');
    }
  }

  function coordsToAlgebraic(r, c) {
    const file = String.fromCharCode(97 + c);
    const rank = 8 - r;
    return `${file}${rank}`;
  }

  function updateUI(data) {
    renderBoard(data.board, data.last_move);
    gameOver = !!data.game_over;

    if (gameOver) {
      const winnerText = data.status === 'checkmate'
        ? (data.winner ? (data.winner === 'white' ? 'White wins by checkmate' : 'Black wins by checkmate') : 'Checkmate')
        : 'Stalemate — draw';
      statusText.textContent = `Game Over: ${winnerText}`;
    } else {
      statusText.textContent = data.current_player === 'white' ? '🟢 Your turn (White)' : '🤖 AI thinking...';
    }

    if (data.last_move) {
      const [[fr, fc], [tr, tc]] = data.last_move;
      lastMoveText.textContent = `Last Move: ${coordsToAlgebraic(fr, fc)} → ${coordsToAlgebraic(tr, tc)}`;
    } else {
      lastMoveText.textContent = '';
    }

    if (data.ai_stats) {
      nodesEvaluatedEl.textContent = (data.ai_stats.nodes_evaluated || 0).toLocaleString();
      nodesPrunedEl.textContent = (data.ai_stats.nodes_pruned || 0).toLocaleString();
      moveTimeEl.textContent = (data.ai_stats.move_time || 0) + ' ms';
    }
  }

  async function onSquareClick(row, col) {
    if (gameOver) return;

    const squareElement = document.querySelector(`.chess-square[data-row='${row}'][data-col='${col}']`);

    // If selecting a destination
    if (selectedSquare) {
      const ok = possibleMoves.find(m => m[0] === row && m[1] === col);
      if (ok) {
        statusText.textContent = 'Processing move...';
        try {
          const res = await fetch('/move', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({from: selectedSquare, to: {row, col}})
          });
          const data = await res.json();
          updateUI(data);
        } catch (e) {
          console.error(e);
        } finally {
          selectedSquare = null;
          possibleMoves = [];
          clearHighlights();
        }
        return;
      }
    }

    // Otherwise (re)select a white piece if it's white's turn
    const pieceSpan = squareElement.querySelector('.piece.white');
    if (pieceSpan && !gameOver) {
      selectedSquare = {row, col};
      clearHighlights();
      squareElement.classList.add('selected');

      try {
        const res = await fetch('/get_possible_moves', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({row, col})
        });
        const data = await res.json();
        possibleMoves = data.possible_moves || [];
        highlightPossibleMoves();
      } catch (e) {
        console.error(e);
      }
    } else {
      // Clicked empty or black piece, clear selection
      selectedSquare = null;
      possibleMoves = [];
      clearHighlights();
    }
  }

  async function bootstrap() {
    try {
      const res = await fetch('/get_state');
      const data = await res.json();
      updateUI(data);
    } catch (e) {
      console.error(e);
    }
  }

  newGameBtn.addEventListener('click', async () => {
    try {
      const res = await fetch('/new_game', {method: 'POST'});
      const data = await res.json();
      selectedSquare = null;
      possibleMoves = [];
      gameOver = false;
      updateUI(data);
    } catch (e) {
      console.error(e);
    }
  });

  bootstrap();
});