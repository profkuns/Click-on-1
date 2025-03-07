from flask import Flask, render_template, request, jsonify, send_file
import csv
import os
import random

app = Flask(__name__)

LOG_FILE = "logs.csv"

# Generate a Pin Sequence with defined rules
@app.route("/generate", methods=["POST"])
def generate_sequence():
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

    # Determine available pin types
    available_types = []
    if standard:
        available_types.append("standard")
    if spool:
        available_types.append("spool")
    if serrated:
        available_types.append("serrated")

    # If no pin types are selected, default to standard
    if not available_types:
        available_types.append("standard")

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
            pin_type = "standard"  # Rule: No spools on 8s
        elif pin_height in [1, 2, 3] and spool and serrated:
            # Rule: Prioritize spools on 1s, 2s, and 3s but allow serrated
            pin_type = random.choices(["spool", "serrated"], weights=[0.7, 0.3])[0]
        elif pin_height in [1, 2, 3] and spool and not serrated:
            pin_type = "spool"
        elif pin_height in [1, 2, 3] and serrated and not spool:
            pin_type = "serrated"
        else:
            pin_type = random.choice(available_types)  # Default selection

        sequence.append({"spot": i + 1, "pin": pin_height, "type": pin_type})
        previous_height = pin_height

    # Log the generated sequence
    save_to_log(pin_count, sequence)

    return jsonify(sequence)


# Save Generated Sequence to Log
def save_to_log(pin_count, sequence):
    log_entry = f"{pin_count} Pin," + ",".join(f"{item['pin']} ({item['type']})" for item in sequence)

    file_exists = os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Lock Type", "Pin Sequence"])  # Write header if file doesn't exist
        writer.writerow([log_entry])

# Export CSV Log
@app.route("/download_log")
def download_log():
    entries = request.args.get("entries", "").strip()
    filter_lock_type = request.args.get("filter", "").strip()

    # Ensure the log file exists and has content
    if not os.path.exists(LOG_FILE) or os.stat(LOG_FILE).st_size == 0:
        return jsonify({"error": "No logs found"}), 404

    with open(LOG_FILE, "r") as file:
        lines = file.readlines()

    if len(lines) < 2:
        return jsonify({"error": "Log file is empty"}), 404

    header = lines[0]
    data = [line.strip() for line in lines[1:] if line.strip()]  # Remove empty lines

    # Filter logs by lock type if specified
    if filter_lock_type:
        data = [line for line in data if filter_lock_type in line.split(",")[0]]

    # Limit entries if specified and is a valid number
    if entries.isdigit():
        entries = int(entries)
        data = data[-entries:]

    # If no data after filtering, return an error
    if not data:
        return jsonify({"error": "No matching log entries found"}), 404

    # Write filtered data to temporary CSV
    temp_file = "filtered_logs.csv"
    with open(temp_file, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(header.strip().split(","))  # Ensure header is written correctly
        for line in data:
            writer.writerow(line.split(","))

    return send_file(temp_file, as_attachment=True, download_name="exported_logs.csv", mimetype="text/csv")


# Clear Log File
@app.route("/clear_log", methods=["POST"])
def clear_log():
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    return jsonify({"message": "Log cleared successfully"})

# Render HTML Page
@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
