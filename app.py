from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

# Hardcoded questions
questions = [
    {"question": "What is 2 + 2?", "options": ["3", "4", "5", "6"], "correct": "4"},
    {"question": "What is the capital of France?", "options": ["Paris", "Berlin", "Rome", "Madrid"], "correct": "Paris"},
    {"question": "What is the color of the sky?", "options": ["Blue", "Green", "Red", "Yellow"], "correct": "Blue"},
    {"question": "What is 5 x 5?", "options": ["10", "20", "25", "30"], "correct": "25"},
]

# Game data
players = {}  # {username: score}
player_answers = {}  # {username: [{question, answer, correct_answer}]}
current_question_index = 0
answers_received = 0
game_pin = "12345"

@app.route("/")
def home():
    return render_template("host.html", game_pin=game_pin)

@app.route("/player/<pin>")
def player(pin):
    if pin == game_pin:
        return render_template("player.html")
    return "Invalid Game PIN", 404

@socketio.on("join_game")
def handle_join(data):
    username = data["username"]
    if username not in players:
        players[username] = 0
        player_answers[username] = []  # Initialize their answer summary
        emit("player_list", list(players.keys()), broadcast=True)

@socketio.on("start_game")
def start_game():
    global current_question_index, answers_received
    current_question_index = 0
    answers_received = 0
    start_next_question()

def start_next_question():
    global current_question_index, answers_received

    if current_question_index >= len(questions):  # End the game if no questions left
        emit_leaderboard()
        socketio.emit("game_over", {"scores": players, "summaries": player_answers})
        return

    # Send the next question
    socketio.emit("new_question", {
        "question": questions[current_question_index]["question"],
        "options": questions[current_question_index]["options"],
        "timer": 10
    })

    # Reset answers for the new question
    answers_received = 0

@socketio.on("submit_answer")
def handle_submit_answer(data):
    global answers_received, current_question_index

    if current_question_index >= len(questions):  # Avoid processing after game over
        return

    username = data["username"]
    answer = data["answer"]
    time_taken = data["time_taken"]  # Time taken to answer

    # Store the player's answer for this question
    correct_answer = questions[current_question_index]["correct"]
    player_answers[username].append({
        "question": questions[current_question_index]["question"],
        "answer": answer,
        "correct_answer": correct_answer
    })

    # Update score if correct
    if answer == correct_answer:
        score = max(100 - time_taken * 10, 0)  # Cap score at 0 if time_taken exceeds 10 seconds
        players[username] += round(score, 4)


    answers_received += 1

    # If all players have submitted, move to the next question
    if answers_received == len(players):
        emit_leaderboard()
        current_question_index += 1
        start_next_question()

def emit_leaderboard():
    # Sort players by score
    sorted_scores = sorted(players.items(), key=lambda x: x[1], reverse=True)
    leaderboard = [{"username": user, "score": score} for user, score in sorted_scores]
    socketio.emit("leaderboard", {"top10": leaderboard})
    
@app.route("/leaderboard")
def leaderboard():
    return render_template("leaderboard.html")

@socketio.on("request_leaderboard")
def handle_leaderboard_request():
    emit_leaderboard()



if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)

