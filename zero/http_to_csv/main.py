import requests
import csv
import argparse
import time
import logging


logging.basicConfig(
    filename='app.log',        
    level=logging.INFO,       
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)


def fetch_user(user_id: str, retries=3, delay=3):
    url = f"https://jsonplaceholder.typicode.com/users/{user_id}"

    for attempt in range(1, retries + 1):
        try:
            logging.info(f"Attempt {attempt}: fetching user {user_id}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            logging.error(f"User {user_id}, attempt {attempt} failed: {e}")
            time.sleep(delay)

    logging.error(f"User {user_id} skipped after {retries} attempts")
    return None


def save_to_csv(users, filename: str):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=';') 
        writer.writerow(["id", "name", "email", "city"])
        for u in users:
            writer.writerow([
                u["id"],
                u["name"],
                u["email"],
                u.get("address", {}).get("city", "")
            ])


def read_ids(filepath: str):
    ids = []

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            value = line.strip()
            if value.isdigit():
                ids.append(value)

    return ids


def save_failed_ids(ids, filename="failed_ids.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(["user_id"])
        for i in ids:
            writer.writerow([i])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Input file with user IDs")
    parser.add_argument("--output", default="result.csv", help="Output CSV file")
    parser.add_argument("--retries", type=int, default=3, help="Number of retry attempts")
    parser.add_argument("--delay", type=int, default=3, help="Delay between retries in seconds")

    args = parser.parse_args()

    logging.info("Script started")

    ids = read_ids(args.input)
    users = []
    failed_ids = []

    for user_id in ids:
        user = fetch_user(user_id, retries=args.retries, delay=args.delay)
        if user:
            users.append(user)
        else:
            failed_ids.append(user_id)

    save_to_csv(users, args.output)

    if failed_ids:
        save_failed_ids(failed_ids)
        logging.warning(f"Failed IDs saved: {len(failed_ids)}")

    logging.info("Script finished successfully")
    print(f"Saved {len(users)} users to {args.output}")

if __name__ == "__main__":
    main()
