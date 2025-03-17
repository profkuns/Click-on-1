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
    "Kwikset KW1": "KW1",
    "Safe": "SAFE"
}

# Generate a Pin Sequence or Safe Combination
@app.route("/generate", methods=["POST"])
def generate_sequence():
    global recent_sequences

    lock_type = request.form.get("lock_type", "American 1100")

    if lock_type == "Safe":
        combo_length = int(request.form.get("combo_length", "3"))
        valid_numbers = [num for num in range(0, 100) if num < 4 or num > 12]  # Exclude 4-12
        combination = random.sample(valid_numbers, combo_length)

        timestamp = datetime.datetime.now().strftime("%m/%d %H:%M")
        formatted_sequence = {
            "type": lock_type_mapping.get(lock_type, lock_type),
            "time": timestamp,
            "pins": combination,
            "types": ["Combination"] * combo_length  # Mark as Combination
        }

        recent_sequences.insert(0, formatted_sequence)
        recent_sequences = recent_sequences[:10]

        return jsonify([{"spot": i + 1, "pin": combination[i], "type": "Combination"} for i in range(combo_length)])

    else:
        pin_count = request.form.get("pins", "6")
        standard = request.form.get("standard", "false") == "true"
        spool = request.form.get("spool", "false") == "true"
        serrated = request.form.get("serrated", "false") == "true"
        hard_mode = request.form.get("hard_mode", "false") == "true"
        macs_mode = request.form.get("macs_mode", "false") == "true" and lock_type in ["Schlage SC1", "Kwikset KW1"]

        try:
            pin_count = int(pin_count)
        except ValueError:
            return jsonify({"error": "Invalid pin count"}), 400

        if lock_type == "Schlage SC1":
            pin_range = list(range(0, 10))
            macs_limit = 7
        elif lock_type == "Kwikset KW1":
            pin_range = list(range(1, 7))
            macs_limit = 4
        else:
            pin_range = list(range(1, 9))
            macs_limit = None  # No MACS mode for A1100

        available_types = []
        if standard:
            available_types.append("standard")
        if spool:
            available_types.append("spool")
        if serrated:
            available_types.append("serrated")

        if not available_types:
            available_types.append("standard")

        sequence = []
        previous_height = None
        highest_pin = min(pin_range)

        for i in range(pin_count):
            pin_height = random.choice(pin_range)

            # Apply MACS mode restrictions only for SC1 and KW1
            if macs_mode and previous_height is not None:
                while abs(pin_height - previous_height) > macs_limit:
                    pin_height = random.choice(pin_range)

            # Hard mode: Ensure large variation between adjacent pins
            if hard_mode and previous_height is not None:
                while abs(pin_height - previous_height) < 2:
                    pin_height = random.choice(pin_range)

            highest_pin = max(highest_pin, pin_height)

            # Determine pin type based on rules
            if lock_type == "Schlage SC1" and pin_height in [0, 1, 2, 3, 4] and spool and serrated:
                pin_type = random.choices(["spool", "serrated"], weights=[0.7, 0.3])[0] if serrated else "spool"
            elif lock_type == "Schlage SC1" and pin_height in [0, 1, 2, 3, 4] and spool:
                pin_type = "spool"
            elif lock_type == "Kwikset KW1" and pin_height in [1, 2, 3] and spool:
                pin_type = "spool"
            elif pin_height == 8:
                pin_type = "standard"
            else:
                pin_type = random.choice(available_types)

            sequence.append({"spot": i + 1, "pin": pin_height, "type": pin_type})
            previous_height = pin_height

        # Ensure at least one standard or serrated pin exists below the highest pin height
        has_non_spool = any(pin["type"] != "spool" for pin in sequence if pin["pin"] < highest_pin)

        if not has_non_spool:
            for pin in sequence:
                if pin["pin"] < highest_pin and pin["type"] == "spool":
                    pin["type"] = "standard" if standard else "serrated" if serrated else "standard"
                    break

        # Ensure no serrated pins appear if serrated is not selected
        if not serrated:
            for pin in sequence:
                if pin["type"] == "serrated":
                    pin["type"] = "standard"

        timestamp = datetime.datetime.now().strftime("%m/%d %H:%M")

        formatted_sequence = {
            "type": lock_type_mapping.get(lock_type, lock_type),
            "time": timestamp,
            "pins": [item["pin"] for item in sequence],
            "types": [item["type"] for item in sequence],
            "macs_mode": macs_mode
        }

        recent_sequences.insert(0, formatted_sequence)
        recent_sequences = recent_sequences[:10]

        return jsonify(sequence)

# Fetch Recent Sequences
@app.route("/recent_sequences")
def get_recent_sequences():
    return jsonify(recent_sequences)

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
