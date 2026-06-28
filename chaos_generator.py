import time
import random
from datetime import datetime

# A list of random components to simulate real application activity
SERVICES = ["OrderAPI", "UserDB", "AuthService", "PaymentGateway", "InventoryAPI"]
LEVELS = ["INFO", "INFO", "WARN", "ERROR", "CRITICAL"] # More INFO logs to look realistic

MESSAGES = [
    "User logged in successfully | UserID: {id}",
    "Outbound API Failure | Target: https://api.stripe.com/v1/charges | Status: {status} | Response: {{'error': 'Timeout'}} | Latency: {latency}ms",
    "Slow Query Detected | Duration: {duration}s | Query: SELECT * FROM products WHERE category_id = {id} ORDER BY price DESC;",
    "Database Connection Pool Exhausted. Active connections: 100. Timeout waiting for connection.",
    "Cache hit for user session | Key: sess_{id}",
    "API Request Inbound | Method: POST | Path: /v1/checkout | Status: {status}"
]

def generate_random_log():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
    service = random.choice(SERVICES)
    level = random.choice(LEVELS)
    
    # If the level is CRITICAL or ERROR, force a bad message
    if level == "CRITICAL":
        msg = MESSAGES[3]
    elif level == "ERROR":
        msg = MESSAGES[1].format(status=random.choice([401, 500, 502]), latency=random.randint(100, 2500))
    elif level == "WARN":
        msg = MESSAGES[2].format(duration=round(random.uniform(1.1, 4.5), 2), id=random.randint(1, 500))
    else:
        msg = random.choice([MESSAGES[0], MESSAGES[4], MESSAGES[5]]).format(id=random.randint(1000, 9999), status=200)
        
    return f"{timestamp} - SERVICE:{service} - LEVEL:{level} - MSG:{msg}\n"

def run_generator():
    print("🚀 Starting Live Chaos Generator...")
    print("Press Ctrl+C to stop it.")
    print("Writing new logs to 'production_logs.txt' every 2 seconds...\n")
    
    while True:
        log_line = generate_random_log()
        print(f"✍️ Generated: {log_line.strip()}")
        
        # Append the new log to our text file
        with open("production_logs.txt", "a", encoding="utf-8") as f:
            f.write(log_line)
            
        time.sleep(2)

if __name__ == "__main__":
    run_generator()