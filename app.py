from flask import Flask, render_template, request, jsonify
import random
import datetime

app = Flask(__name__)

# Store the last 10 sequences in memory
recent_sequences = []

# Mapping for shortened lock types
lock_type_mapping = {
    "American 1100": "A1100",
    "Schlage SC1": "SC1",
    "Kwikset KW1": "KW1"
}

# Generate a Pin Sequence
@app.route("/generate", methods=["POST"])
def generate_sequence():
    global recent_sequences

    lock_type = request.form.get("lock_type", "American 1100")  # Get lock type selection
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

    # Set pin height range based on lock type
    if lock_type == "Schlage SC1":
        pin_range = range(0, 10)  # SC1 uses pins from 0-9
    elif lock_type == "Kwikset KW1":
        pin_range = range(1, 7)  # KW1 uses pins from 1-6
    else:
        pin_range = range(1, 9)  # Default A1100 uses 1-8

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
    highest_pin = min(pin_range)

    for i in range(pin_count):
        pin_height = random.choice(pin_range)

        # Hard mode: Ensure large variation between adjacent pins
        if hard_mode and previous_height is not None:
            while abs(pin_height - previous_height) < 2:
                pin_height = random.choice(pin_range)

        highest_pin = max(highest_pin, pin_height)  # Track the highest pin height

        # Determine pin type based on rules
        if lock_type == "Schlage SC1" and pin_height in [0, 1, 2, 3, 4] and spool and serrated:
            pin_type = random.choices(["spool", "serrated"], weights=[0.7, 0.3])[0] if serrated else "spool"
        elif lock_type == "Schlage SC1" and pin_height in [0, 1, 2, 3, 4] and spool:
            pin_type = "spool"
        elif lock_type == "Kwikset KW1" and pin_height in [1, 2, 3] and spool:
            pin_type = "spool"
        elif pin_height == 8:  # Default rule for 8s
            pin_type = "standard"
        else:
            pin_type = random.choice(available_types)

        sequence.append({"spot": i + 1, "pin": pin_height, "type": pin_type})
        previous_height = pin_height

    # Ensure at least one standard or serrated pin exists below the highest pin height
    has_non_spool = any(pin["type"] != "spool" for pin in sequence if pin["pin"] < highest_pin)

    if not has_non_spool:
        # Force a change in one of the lower spots to standard or serrated
        for pin in sequence:
            if pin["pin"] < highest_pin and pin["type"] == "spool":
                pin["type"] = "standard" if standard else "serrated" if serrated else "standard"
                break  # Stop after making one change

    # Ensure no serrated pins appear if serrated is not selected
    if not serrated:
        for pin in sequence:
            if pin["type"] == "serrated":
                pin["type"] = "standard"

    # Generate timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Convert sequence to table format with lock type (shortened format)
    formatted_sequence = {
        "type": lock_type_mapping.get(lock_type, lock_type),  # Convert to A1100, SC1, or KW1
        "time": timestamp,
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
