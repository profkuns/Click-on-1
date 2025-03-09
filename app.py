from flask import Flask, render_template, request, jsonify
import random
import datetime

app = Flask(__name__)

# Store the last 10 sequences in memory
recent_sequences = []

# Generate a Pin Sequence
@app.route("/generate", methods=["POST"])
def generate_sequence():
    global recent_sequences

    pin_count = request.form.get("pins", "6")  
    standard = request.form.get("standard", "false") == "true"
    spool = request.form.get("spool", "false") == "true"
    serrated = request.form.get("serrated", "false") == "true"
    hard_mode = request.form.get("hard_mode", "false") == "true"

    # Ensure pin count is an integer
    try:
        pin_count = int(pin_count)
    except ValueError:
        return jsonify({"error": "Invalid pin count"}), 400

    available_types = []
    if standard:
        available_types.append("standard")
    if spool:
        available_types.append("spool")
    if serrated:
        available_types.append("serrated")

    if not available_types:
        available_types.append("standard")  # Default to standard if none are selected

    sequence = []
    previous_height = None

    for i in range(pin_count):
        pin_height = random.randint(1, 8)

        # Hard mode: Ensure large variation between adjacent pins
        if hard_mode and previous_height is not None:
            while abs(pin_height - previous_height) < 2:
                pin_height = random.randint(1, 8)

        # Determine pin type based on rules
        if pin_height == 8:
            pin_type = "standard"
        elif pin_height in [1, 2, 3] and spool and serrated:
            pin_type = random.choices(["spool", "serrated"], weights=[0.7, 0.3])[0]
        elif pin_height in [1, 2, 3] and spool:
            pin_type = "spool"
        elif pin_height in [1, 2, 3] and serrated:
            pin_type = "serrated"
        else:
            pin_type = random.choice(available_types)

        # Explicitly add spot number
        sequence.append({"spot": i + 1, "pin": pin_height, "type": pin_type})
        previous_height = pin_height

    # Generate timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Convert sequence to A1100 table format with timestamp
    formatted_sequence = {
        "type": "A1100",
        "timestamp": timestamp,
        "pins": [item["pin"] for item in sequence],
        "types": [item["type"] for item in sequence]
    }

    # Store in recent sequences (keep only last 10)
    recent_sequences.insert(0, formatted_sequence)
    recent_sequences = recent_sequences[:10]

    return jsonify(sequence)

# Fetch Recent Sequences for Display
@app.route("/recent_sequences", methods=["GET"])
def get_recent_sequences():
    return jsonify(recent_sequences)

# Render HTML Page
@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
