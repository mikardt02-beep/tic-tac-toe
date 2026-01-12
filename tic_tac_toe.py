import turtle
import random
import pickle

# -------------------------
# Files used by the game
# -------------------------
SAVE_FILE = "tictactoe_save.bin"      # Binary save file (pickle)
HISTORY_FILE = "game_history.txt"     # Text file: Player1,Player2,Winner


# -------------------------
# History handling
# -------------------------
def append_game_history(p1, p2, winner):
    """Append one finished game to the history file: p1,p2,winner"""
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(f"{p1},{p2},{winner}\n")


def read_game_history():
    """Read all history lines from the text file (if exists)."""
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return [line.strip() for line in lines if line.strip()]
    except FileNotFoundError:
        return []
    except (OSError, UnicodeDecodeError):
        return []


def show_game_history(screen):
    """Print the full history to console and also show it in a popup."""
    lines = read_game_history()

    print("\n===== GAME HISTORY =====")
    if not lines:
        print("No games history yet.")
        msg = "No games history yet."
    else:
        for line in lines:
            print(line)
        msg = "\n".join(lines)
    print("========================\n")

    screen.textinput("Game History", msg + "\n\n(Press OK to continue)")


# -------------------------
# Save / Load handling
# -------------------------
def save_game(filename, board, current_player, mode, name1, name2, vs_computer, computer_strategy):
    """Save the current game state into a binary file using pickle."""
    data = {
        "board": board,
        "current_player": current_player,
        "mode": mode,
        "name1": name1,
        "name2": name2,
        "vs_computer": vs_computer,
        "computer_strategy": computer_strategy
    }
    with open(filename, "wb") as f:
        pickle.dump(data, f)  # type: ignore[arg-type]
    print("Game saved!")


def load_game(filename):
    """Load a saved game state from a binary file."""
    with open(filename, "rb") as f:
        return pickle.load(f)


# -------------------------
# Drawing helpers
# -------------------------
def redraw_from_board(screen, board):
    """Clear the screen and redraw the grid + all existing moves."""
    screen.clear()
    drow_board()

    for r in range(3):
        for c in range(3):
            if board[r][c] == "X":
                draw_x(r, c)
            elif board[r][c] == "O":
                drow_circle(r, c)


def new_game_prompt(screen):
    """Ask the user if they want to start a new game after the current one ends."""
    ans = screen.textinput("Game Over", "Play again? (Y/N)")
    if ans is None:
        return False
    return ans.strip().upper() == "Y"


def exit_game(screen, message="Game ended."):
    """Close the turtle window gracefully and print a message."""
    print(message)
    try:
        screen.bye()
    except turtle.Terminator:
        pass


# -------------------------
# Setup helpers (start / mode / names)
# -------------------------
def setup_new_game(screen):
    """
    Full setup flow: choose mode + player names, create empty board, draw board.
    Returns:
        (board, current_player, mode, name1, name2, vs_computer, computer_strategy)
    If user cancels at any step -> returns None
    """
    mode = screen.textinput(
        "Game Mode",
        "Choose mode:\n"
        "1 = Player vs Player\n"
        "2 = Player vs Random Computer\n"
        "3 = Player vs Strategic Computer"
    )
    if mode is None:
        return None
    mode = (mode.strip() or "1")

    name1_input = screen.textinput("Player 1", "Enter Player 1 name (X):")
    if name1_input is None:
        return None
    name1 = name1_input.strip() or "Player 1"

    vs_computer = False
    computer_strategy = "none"

    if mode == "2":
        name2 = "Computer (Random)"
        vs_computer = True
        computer_strategy = "random"
    elif mode == "3":
        name2 = "Computer (Strategic)"
        vs_computer = True
        computer_strategy = "strategic"
    else:
        name2_input = screen.textinput("Player 2", "Enter Player 2 name (O):")
        if name2_input is None:
            return None
        name2 = name2_input.strip() or "Player 2"

    board = [["" for _ in range(3)] for _ in range(3)]
    current_player = "X"
    redraw_from_board(screen, board)

    return board, current_player, mode, name1, name2, vs_computer, computer_strategy


def setup_from_start(screen):
    """
    Start screen: New or Load.
    Returns the same tuple as setup_new_game, or None if user cancels at start.
    """
    start_choice = screen.textinput("Start", "Type:\nN = New Game\nL = Load Saved Game")
    if start_choice is None:
        return None

    start_choice = (start_choice.strip().upper() or "N")

    if start_choice == "L":
        try:
            data = load_game(SAVE_FILE)
            board = data["board"]
            current_player = data["current_player"]
            mode = data["mode"]
            name1 = data["name1"]
            name2 = data["name2"]
            vs_computer = data["vs_computer"]
            computer_strategy = data["computer_strategy"]
            redraw_from_board(screen, board)
            print("Game loaded!")
            return board, current_player, mode, name1, name2, vs_computer, computer_strategy
        except FileNotFoundError:
            print("No saved game file found. Starting a new game...")
        except (EOFError, pickle.UnpicklingError, OSError):
            print("Save file is corrupted or unreadable. Starting a new game...")

    # Always fall back to creating a new game
    return setup_new_game(screen)


# -------------------------
# Main game loop
# -------------------------
def main():
    screen = turtle.Screen()
    screen.title("Tic Tac Toe")

    state = setup_from_start(screen)
    if state is None:
        exit_game(screen, "Game ended by user (cancelled at start).")
        return

    board, current_player, mode, name1, name2, vs_computer, computer_strategy = state

    # Allow playing multiple rounds without rerunning the script
    while True:
        game_over = False

        while not game_over:
            # Computer move
            if vs_computer and current_player == "O":
                if computer_strategy == "strategic":
                    move = strategic_move(board, computer="O", human="X")
                    if move is None:
                        # Shouldn't really happen, but just in case
                        exit_game(screen, "No moves left.")
                        return
                    row, col = move
                else:
                    empties = empty_cells(board)
                    if not empties:
                        exit_game(screen, "No moves left.")
                        return
                    row, col = random.choice(empties)

            else:
                # Human move / commands
                player_name = name1 if current_player == "X" else name2

                row_input = screen.textinput(
                    "Input",
                    f"{player_name} ({current_player})\n"
                    "Enter row (1-3)\n"
                    "or S = Save, L = Load, H = History, R = Restart"
                )

                # If user closes the dialog -> exit the game
                if row_input is None:
                    exit_game(screen, "Game ended by user.")
                    return

                row_input = row_input.strip().upper()

                # Full restart: go back to mode + player names
                if row_input == "R":
                    print("Full restart requested. Starting setup again...")
                    new_state = setup_new_game(screen)
                    if new_state is None:
                        exit_game(screen, "Game ended by user (cancelled during restart setup).")
                        return
                    board, current_player, mode, name1, name2, vs_computer, computer_strategy = new_state
                    continue

                # Save
                if row_input == "S":
                    save_game(SAVE_FILE, board, current_player, mode, name1, name2, vs_computer, computer_strategy)
                    continue

                # Load
                if row_input == "L":
                    try:
                        data = load_game(SAVE_FILE)
                        board = data["board"]
                        current_player = data["current_player"]
                        mode = data["mode"]
                        name1 = data["name1"]
                        name2 = data["name2"]
                        vs_computer = data["vs_computer"]
                        computer_strategy = data["computer_strategy"]
                        redraw_from_board(screen, board)
                        print("Game loaded!")
                    except FileNotFoundError:
                        print("No saved game file found.")
                    except (EOFError, pickle.UnpicklingError, OSError):
                        print("Load failed (corrupted or unreadable save file).")
                    continue

                # History
                if row_input == "H":
                    show_game_history(screen)
                    continue

                # Validate row number
                if not row_input.isdigit() or not (1 <= int(row_input) <= 3):
                    print("Invalid row input.")
                    continue

                row = int(row_input) - 1

                col = screen.numinput(
                    "Input",
                    f"{player_name} ({current_player}) - Enter column (1-3):",
                    default=1, minval=1, maxval=3
                )
                if col is None:
                    exit_game(screen, "Game ended by user.")
                    return
                col = int(col) - 1

            # Validate the chosen cell
            if board[row][col] != "":
                if vs_computer and current_player == "O":
                    continue
                print("Cell already taken.")
                continue

            # Apply move and draw it
            board[row][col] = current_player
            if current_player == "X":
                draw_x(row, col)
            else:
                drow_circle(row, col)

            # Win / Draw check
            win_cells = get_win_cells(board, current_player)
            if win_cells:
                winner_name = name1 if current_player == "X" else name2
                print(f"{winner_name} ({current_player}) WIN!")
                draw_win_line(win_cells)
                append_game_history(name1, name2, winner_name)
                game_over = True

            elif board_full(board):
                print("It's a DRAW!")
                append_game_history(name1, name2, "DRAW")
                game_over = True

            else:
                current_player = "O" if current_player == "X" else "X"

        # After the game ends, ask if user wants another round
        if new_game_prompt(screen):
            print("Starting a new game...")
            board = [["" for _ in range(3)] for _ in range(3)]
            current_player = "X"
            redraw_from_board(screen, board)
        else:
            exit_game(screen, "Game ended.")
            return


# -------------------------
# Board drawing + symbols
# -------------------------
def drow_board():
    """Draw the tic-tac-toe grid."""
    bob = turtle.Turtle()
    bob.color("blue", "cyan")
    bob.speed(0)
    bob.hideturtle()

    bob.penup()
    bob.goto(-90, -30)
    bob.pendown()
    bob.goto(90, -30)

    bob.penup()
    bob.goto(90, 30)
    bob.pendown()
    bob.goto(-90, 30)

    bob.penup()
    bob.goto(30, 90)
    bob.pendown()
    bob.goto(30, -90)

    bob.penup()
    bob.goto(-30, 90)
    bob.pendown()
    bob.goto(-30, -90)


def draw_x(row, col):
    """Draw X in the given cell."""
    t = turtle.Turtle()
    t.hideturtle()
    t.speed(1)

    x = (col - 1) * 60
    y = (1 - row) * 60

    t.penup()
    t.goto(x - 20, y - 20)
    t.pendown()
    t.goto(x + 20, y + 20)

    t.penup()
    t.goto(x - 20, y + 20)
    t.pendown()
    t.goto(x + 20, y - 20)


def drow_circle(row, col):
    """Draw O in the given cell."""
    t = turtle.Turtle()
    t.hideturtle()
    t.speed(1)

    x = (col - 1) * 60
    y = (1 - row) * 60

    t.penup()
    t.goto(x, y - 20)
    t.pendown()
    t.circle(20)


# -------------------------
# Game logic helpers
# -------------------------
def board_full(board):
    """Return True if the board has no empty cells."""
    for r in range(3):
        for c in range(3):
            if board[r][c] == "":
                return False
    return True


def get_win_cells(board, p):
    """Return the 3 winning cells (row,col) if player p won, else None."""
    # Rows
    for i in range(3):
        if board[i][0] == p and board[i][1] == p and board[i][2] == p:
            return [(i, 0), (i, 1), (i, 2)]

    # Columns
    for i in range(3):
        if board[0][i] == p and board[1][i] == p and board[2][i] == p:
            return [(0, i), (1, i), (2, i)]

    # Diagonals
    if board[0][0] == p and board[1][1] == p and board[2][2] == p:
        return [(0, 0), (1, 1), (2, 2)]

    if board[0][2] == p and board[1][1] == p and board[2][0] == p:
        return [(0, 2), (1, 1), (2, 0)]

    return None


def cell_center(row, col):
    """Convert board (row,col) to turtle screen center point of that cell."""
    x = (col - 1) * 60
    y = (1 - row) * 60
    return x, y


def draw_win_line(cells):
    """Draw a red line across the winning 3 cells."""
    (r1, c1) = cells[0]
    (r3, c3) = cells[2]

    x1, y1 = cell_center(r1, c1)
    x3, y3 = cell_center(r3, c3)

    line = turtle.Turtle()
    line.hideturtle()
    line.speed(0)
    line.pensize(6)
    line.color("red")

    dx = x3 - x1
    dy = y3 - y1
    length = (dx * dx + dy * dy) ** 0.5

    if length != 0:
        ux = dx / length
        uy = dy / length
    else:
        ux = 0
        uy = 0

    overshoot = 35
    start_x = x1 - ux * overshoot
    start_y = y1 - uy * overshoot
    end_x = x3 + ux * overshoot
    end_y = y3 + uy * overshoot

    line.penup()
    line.goto(start_x, start_y)
    line.pendown()
    line.goto(end_x, end_y)


def empty_cells(board):
    """Return a list of all empty cells."""
    cells = []
    for r in range(3):
        for c in range(3):
            if board[r][c] == "":
                cells.append((r, c))
    return cells


def strategic_move(board, computer="O", human="X"):
    """Simple strategy: win, block, center, corners, sides."""
    # 1) Win if possible
    for (r, c) in empty_cells(board):
        board[r][c] = computer
        if get_win_cells(board, computer):
            board[r][c] = ""
            return r, c
        board[r][c] = ""

    # 2) Block opponent win
    for (r, c) in empty_cells(board):
        board[r][c] = human
        if get_win_cells(board, human):
            board[r][c] = ""
            return r, c
        board[r][c] = ""

    # 3) Take center
    if board[1][1] == "":
        return 1, 1

    # 4) Try corners
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    available_corners = [(r, c) for (r, c) in corners if board[r][c] == ""]
    if available_corners:
        return random.choice(available_corners)

    # 5) Try sides
    sides = [(0, 1), (1, 0), (1, 2), (2, 1)]
    available_sides = [(r, c) for (r, c) in sides if board[r][c] == ""]
    if available_sides:
        return random.choice(available_sides)

    return None


if __name__ == "__main__":
    main()

