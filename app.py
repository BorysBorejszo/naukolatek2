from flask import Flask, render_template, jsonify, request
import qrcode
from io import BytesIO
import base64
import time
import paramiko

app = Flask(__name__)

# Simulated product data with images
products = [
    {"id": 1, "name": "Koszulka infotech", "price": 50, "image": "product_a.png"},
    {"id": 2, "name": "Kubek Infotech", "price": 75, "image": "product_b.png"},
    {"id": 3, "name": "Kaczucha Infotech", "price": 100, "image": "product_c.png"},
    {"id": 4, "name": "Etui Infotech", "price": 150, "image": "product_d.png"},
]

ICP_ADDRESS = "lf5mq-ygcgt-vrtka-sygwu-mlbw2-4u256-yxkfm-wik7i-2qo3d-3pqkx-lae"
TOKEN_CANISTER_ID = "tbsjh-jyaaa-aaaad-qg7nq-cai"
PASSWORD = "Lol12345@"


# Function to get balance using SSH
def get_balance():
    """
    Uses paramiko to SSH into the VPS and run the script to get the balance.
    Converts the balance from nats to coins (divide by 1000).
    """
    host = "10.192.192.145"
    user = "pawel"
    password = "%!5K4zmjEYnnZuK&4#7*WsfVj"
    command = "bash ~/komenda.sh"

    try:
        print("[INFO] Nawiązywanie połączenia SSH...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh.connect(hostname=host, username=user, password=password)
        print("[OK] Połączono z VPS.")

        print(f"\n[INFO] Wykonuję skrypt: {command}")

        stdin, stdout, stderr = ssh.exec_command(command)

        output = stdout.read().decode().strip()
        error = stderr.read().decode()

        print("[INFO] Zamykam połączenie SSH...")
        ssh.close()
        print("[OK] Połączenie zamknięte.")

        print("\n[WYNIK]:")
        print(output)

        if error:
            print("\n[BŁĄD]:")
            print(error)

        # Clean up the output to extract the numeric balance (in nats)
        balance_str = output.split(' ')[0].replace('_', '').replace('(', '').replace(')', '').replace(':', '').strip()

        # Now, try to convert the balance string into an integer (in nats)
        balance_in_nats = int(balance_str)

        # Convert nats to coins by dividing by 1000
        balance_in_coins = balance_in_nats / 1000.0

        # Return the balance in coins
        return balance_in_coins

    except paramiko.AuthenticationException:
        print("[BŁĄD] Nie udało się zalogować! Sprawdź dane logowania.")
    except paramiko.SSHException as e:
        print(f"[BŁĄD] Błąd SSH: {e}")
    except Exception as e:
        print(f"[BŁĄD] Nieznany błąd: {e}")
    return None


@app.route('/')
def index():
    return render_template('index.html', products=products)


@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    data = request.json
    product_id = data.get('product_id')
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
    product = next((p for p in products if p['id'] == product_id), None)
    if not product:
        return jsonify({"status": "error", "message": "Produkt nie znaleziony"}), 404

    product_price = product['price']

    try:
        initial_balance = get_balance()
        if initial_balance is None:
            raise ValueError("Initial balance fetch failed")
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error fetching initial balance: {e}"}), 500

    # Check for payment every 5 seconds up to 10 times
    max_checks = 10
    attempts = 0
    new_balance = initial_balance

    while attempts < max_checks:
        time.sleep(5)
        try:
            new_balance = get_balance()
            if new_balance is None:
                raise ValueError("New balance fetch failed")
        except Exception as e:
            return jsonify({"status": "error", "message": f"Error fetching new balance: {e}"}), 500

        # Formatting balance as a more readable number
        formatted_balance = f"{new_balance:,.2f} coins"

        # Check if payment has been completed
        if new_balance >= initial_balance + product_price:
            return jsonify({"status": "success", "balance": formatted_balance})

        attempts += 1

    # If after the loop the payment hasn't been completed
    return jsonify({"status": "pending", "message": "Płatność nie zakończona lub niewystarczająca kwota.", "balance": formatted_balance})


if __name__ == '__main__':
    app.run(debug=True)
