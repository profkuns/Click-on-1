from flask import Flask, render_template, request, jsonify, send_file
import csv
import os
import datetime

app = Flask(__name__)

LOG_FILE = "logs.csv"

# Generate Pin Sequence and Log It
@app.route("/generate", methods=["POST"])
def generate_sequence():
    pin_count = request.form.get("pins", "6 Pin")
    standard = request.form.get("standard", "false") == "true"
    spool = request.form.get("spool", "false") == "true"
    serrated = request.form.get("serrated", "false") == "true"
    hard_mode = request.form.get("hard_mode", "false") == "true"
    
    # Sample generated pins (replace with actual generation logic)
    sequence = [
        {"spot": i + 1, "pin": i + 2, "type": "spool" if spool else "standard"} for i in range(int(pin_count[0]))
    ]
    
    # Get timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Log entry
    log_data = [[timestamp, pin_count, item["spot"], item["pin"], item["type"], "Yes" if hard_mode else "No"] for item in sequence]
    
    # Save to CSV
    file_exists = os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Timestamp", "Lock Type", "Spot", "Pin Height", "Pin Type", "Hard Mode"])
        writer.writerows(log_data)
        writer.writerow([])  # Blank line to separate entries

    return jsonify(sequence)

# Export CSV Log
@app.route("/download_log")
def download_log():
    entries = int(request.args.get("entries", 0))
    filter_lock_type = request.args.get("filter", "").strip()

    # Read log file
    if not os.path.exists(LOG_FILE):
        return jsonify({"error": "No logs found"}), 404

    with open(LOG_FILE, "r") as file:
        lines = file.readlines()

    # Filter logs if needed
    header = lines[0]
    data = [line for line in lines[1:] if line.strip()]
    
    if filter_lock_type:
        data = [line for line in data if line.split(",")[1].strip() == filter_lock_type]

    if entries > 0:
        data = data[-entries:]

    # Write filtered data to temporary CSV
    temp_file = "filtered_logs.csv"
    with open(temp_file, "w", newline="") as file:
        file.writelines([header] + data)

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
