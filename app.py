from flask import Flask, render_template, request, jsonify, send_file
import csv
import random
import os

app = Flask(__name__, static_folder="static")

LOG_FILE = "lock_log.csv"

# Function to generate lock sequences with optional Hard Mode
def generate_lock_sequence(num_pins, enabled_pins, hard_mode):
    sequence = []
    previous_pin = None  # Track last pin for Hard Mode calculations

    # Ensure at least one pin type is enabled (fallback to "standard")
    if not any(enabled_pins.values()):
        enabled_pins["standard"] = True

    for i in range(num_pins):
        if hard_mode:
            # Generate numbers with high variation (large standard deviation)
            if previous_pin is None:
                pin = random.randint(1, 8)
            else:
                valid_pins = [p for p in range(1, 9) if abs(p - previous_pin) >= 3]
                pin = random.choice(valid_pins)
        else:
            # Normal mode: Random selection from 1 to 8
            pin = random.randint(1, 8)

        previous_pin = pin  # Store for next loop iteration

        # Build the list of allowed pin types
        possible_types = []
        if enabled_pins["standard"]:
            possible_types.append("standard")
        if enabled_pins["spool"]:
            possible_types.append("spool")
        if enabled_pins["serrated"]:
            possible_types.append("serrated")

        # Ensure at least one type is available
        if not possible_types:
            possible_types.append("standard")

        # Determine pin type based on rules and enabled pin types
        if pin == 7:
            lock_type = "serrated" if "serrated" in possible_types else random.choice(possible_types)
        elif pin in [1, 2, 3]:
            if "spool" in possible_types and "serrated" in possible_types:
                lock_type = random.choices(["spool", "serrated"], weights=[0.75, 0.25])[0]
            elif "spool" in possible_types:
                lock_type = "spool"
            elif "serrated" in possible_types:
                lock_type = "serrated"
            else:
                lock_type = "standard"
        else:
            lock_type = random.choice(possible_types)

        sequence.append({"spot": i + 1, "pin": pin, "type": lock_type})

    log_sequence(num_pins, sequence)
    return sequence

# Log sequences to CSV
def log_sequence(num_pins, sequence):
    with open(LOG_FILE, "a", newline="") as file:
        writer = csv.writer(file)
        for row in sequence:
            writer.writerow([num_pins, row["spot"], row["pin"], row["type"]])

# Clear log file
@app.route("/clear_log", methods=["POST"])
def clear_log():
    open(LOG_FILE, "w").close()
    return jsonify({"message": "Log cleared!"})

# Generate lock sequences
@app.route("/generate", methods=["POST"])
def generate():
    num_pins = int(request.form.get("pins", 6))
    hard_mode = request.form.get("hard_mode") == "true"
    
    enabled_pins = {
        "standard": request.form.get("standard") == "true",
        "spool": request.form.get("spool") == "true",
        "serrated": request.form.get("serrated") == "true",
    }

    return jsonify(generate_lock_sequence(num_pins, enabled_pins, hard_mode))

# Download log file with filtering options
@app.route("/download_log", methods=["GET"])
def download_log():
    entries = request.args.get("entries", "0")
    filter_type = request.args.get("filter", "0")

    if not os.path.exists(LOG_FILE):
        return jsonify({"message": "No logs available."}), 404

    with open(LOG_FILE, "r") as file:
        reader = list(csv.reader(file))

    if filter_type != "0":
        reader = [row for row in reader if row[0] == filter_type]

    if entries != "0":
        reader = reader[-int(entries):]

    temp_file = "filtered_log.csv"
    with open(temp_file, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Lock Type", "Spot", "Pin Number", "Type"])
        writer.writerows(reader)

    return send_file(temp_file, as_attachment=True)

# Serve the frontend page
@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
