from flask import Flask, render_template, request, jsonify, send_file
import csv
import os
import datetime
import random

app = Flask(__name__)

LOG_FILE = "logs.csv"

# Generate a Pin Sequence
@app.route("/generate", methods=["POST"])
def generate_sequence():
    pin_count = request.form.get("pins", "6")  
    standard = request.form.get("standard", "false") == "true"
    spool = request.form.get("spool", "false") == "true"
    serrated = request.form.get("serrated", "false") == "true"
    hard_mode = request.form.get("hard_mode", "false") == "true"

    # Ensure pin count is an integer
    try:
        pin_count = int(pin_count[0])  # Extract number from "6 Pin" string
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

        if hard_mode and previous_height is not None:
            while abs(pin_height - previous_height) < 2:  # Ensure variation
                pin_height = random.randint(1, 8)

        pin_type = random.choice(available_types)
        sequence.append({"spot": i + 1, "pin": pin_height, "type": pin_type})
        previous_height = pin_height

    return jsonify(sequence)


# Export CSV Log
@app.route("/download_log")
def download_log():
    entries = int(request.args.get("entries", 0))
    filter_lock_type = request.args.get("filter", "").strip()

    # Check if log file exists
    if not os.path.exists(LOG_FILE) or os.stat(LOG_FILE).st_size == 0:
        return jsonify({"error": "No logs found"}), 404

    with open(LOG_FILE, "r") as file:
        lines = file.readlines()

    if len(lines) < 2:
        return jsonify({"error": "Log file is empty"}), 404

    header = lines[0]
    data = [line.strip() for line in lines[1:] if line.strip()]  # Remove empty lines

    # Filter logs by lock type
    if filter_lock_type:
        data = [line for line in data if filter_lock_type in line.split(",")[1]]

    # Limit entries if specified
    if entries > 0:
        data = data[-entries:]

    # If no data after filtering, return an error
    if not data:
        return jsonify({"error": "No matching log entries found"}), 404

    # Write filtered data to temporary CSV
    temp_file = "filtered_logs.csv"
    with open(temp_file, "w", newline="") as file:
        file.writelines([header] + [line + "\n" for line in data])

    return send_file(temp_file, as_attachment=True, download_name="exported_logs.csv")

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
