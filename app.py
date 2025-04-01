from flask import Flask, render_template, jsonify, request
import qrcode
from io import BytesIO
import base64
import time
import requests
import json

app = Flask(__name__)

# Simulated product data with images
products = [
    {"id": 1, "name": "Koszulka infotech", "price": 50, "image": "product_a.png"},
    {"id": 2, "name": "Kubek Infotech", "price": 75, "image": "product_b.png"},
    {"id": 3, "name": "Kaczucha Infotech", "price": 100, "image": "product_c.png"},
    {"id": 4, "name": "Etui Infotech", "price": 150, "image": "product_d.png"},
]

# ICP address and token canister ID
ICP_ADDRESS = "lf5mq-ygcgt-vrtka-sygwu-mlbw2-4u256-yxkfm-wik7i-2qo3d-3pqkx-lae"
TOKEN_CANISTER_ID = "ryjl3-tyaaa-aaaaa-aaaba-cai"  # Replace with actual canister ID


# Corrected HTTP request to query the balance
def get_balance_via_http(wallet_address):
    """
    Query the balance of tokens for the given wallet address using an HTTP request to the IC API.
    """
    try:
        url = f"https://ic0.app/api/v2/canister/{TOKEN_CANISTER_ID}/query"
        headers = {
            "Content-Type": "application/json"
        }
        # Create the correct payload structure
        payload = {
            "request_type": "query",
            "canister_id": TOKEN_CANISTER_ID,
            "method_name": "icrc1_balance_of",
            "arg": {
                "owner": {
                    "principal": wallet_address
                }
            }
        }

        # Convert the payload to JSON format
        payload_json = json.dumps(payload)

        # Send the HTTP POST request
        response = requests.post(url, data=payload_json, headers=headers)
        response.raise_for_status()  # Check for HTTP errors
        # Return the result from the response JSON
        return response.json().get('result')

    except Exception as e:
        print(f"Error fetching balance via HTTP: {e}")
        return None


@app.route('/')
def index():
    return render_template('index.html', products=products)


@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    data = request.json
    product_id = data.get('product_id')
    # Generate QR code data including the ICP address and product id as a query parameter.
    qr_data = f"{ICP_ADDRESS}"
    img = qrcode.make(qr_data)
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return jsonify({"qr_code": qr_base64})


@app.route('/check_payment', methods=['POST'])
def check_payment():
    data = request.json
    product_id = data.get('product_id')

    # Find the product details by product id
    product = next((p for p in products if p['id'] == product_id), None)
    if not product:
        return jsonify({"status": "error", "message": "Produkt nie znaleziony"}), 404

    product_price = product['price']
    wallet_address = ICP_ADDRESS

    try:
        # Get the initial balance before payment
        initial_balance = get_balance_via_http(wallet_address)
        if initial_balance is None:
            raise ValueError("Initial balance fetch failed")
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error fetching initial balance: {e}"}), 500

    # Wait for 5 seconds
    time.sleep(5)

    try:
        # Get the new balance after waiting
        new_balance = get_balance_via_http(wallet_address)
        if new_balance is None:
            raise ValueError("New balance fetch failed")
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error fetching new balance: {e}"}), 500

    # Check if the balance increased by at least the price of the product
    if new_balance is not None and new_balance - 1 >= initial_balance + product_price:
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "pending", "message": "Płatność nie zakończona lub niewystarczająca kwota."})


if __name__ == '__main__':
    app.run(debug=True)
