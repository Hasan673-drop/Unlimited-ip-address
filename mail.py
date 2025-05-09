import requests
import json
import random
import string
import os

class MailTmAPI:
    def __init__(self, base_url="https://api.mail.tm"):
        self.base_url = base_url

    def get_domains(self):
        """Fetches available domains from the Mail.tm API."""
        try:
            response = requests.get(f"{self.base_url}/domains")
            response.raise_for_status()
            data = response.json()
            domains = [domain['domain'] for domain in data['hydra:member']]
            return domains
        except requests.exceptions.RequestException as e:
            print(f"Error fetching domains: {e}")
            return None

    def create_account(self, username, password, domain):
        """Creates a new temporary email account."""
        address = f"{username}@{domain}"
        payload = {
            "address": address,
            "password": password
        }
        headers = {
            'Content-Type': 'application/json'
        }
        try:
            response = requests.post(f"{self.base_url}/accounts", headers=headers, json=payload)
            response.raise_for_status()
            account_data = response.json()

            # Get the token immediately after account creation
            token_response = self.get_token(address, password)
            if token_response and 'token' in token_response:
                account_data['token'] = token_response['token']
                account_data['address'] = address
                return account_data
            else:
                print("Error getting token after account creation.")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Error creating account: {e}")
            if response.status_code == 422:
                print("Account creation failed. Possible issues: Username too short, invalid domain, or username already taken.")
            return None

    def get_token(self, address, password):
        """Retrieves an authentication token for an existing account."""
        payload = {
            "address": address,
            "password": password
        }
        headers = {
            'Content-Type': 'application/json'
        }
        try:
            response = requests.post(f"{self.base_url}/token", headers=headers, json=payload)
            response.raise_for_status()
            token_data = response.json()
            return token_data
        except requests.exceptions.RequestException as e:
            print(f"Error getting token: {e}")
            return None

    def get_messages(self, token):
        """Retrieves a list of messages for the authenticated account."""
        headers = {
            'Authorization': f'Bearer {token}'
        }
        try:
            response = requests.get(f"{self.base_url}/messages", headers=headers)
            response.raise_for_status()
            messages_data = response.json()
            messages = messages_data['hydra:member']
            return messages
        except requests.exceptions.RequestException as e:
            print(f"Error fetching messages: {e}")
            if response.status_code == 401:
                print("Authentication failed. Invalid token.")
            return None

    def get_message_content(self, token, message_id):
        """Retrieves the full content of a specific message."""
        headers = {
            'Authorization': f'Bearer {token}'
        }
        try:
            response = requests.get(f"{self.base_url}/messages/{message_id}", headers=headers)
            response.raise_for_status()
            message_content = response.json()
            return message_content
        except requests.exceptions.RequestException as e:
            print(f"Error fetching message content for ID {message_id}: {e}")
            if response.status_code == 401:
                print("Authentication failed. Invalid token.")
            if response.status_code == 404:
                print("Message not found.")
            return None

def generate_random_username(length=10):
    """Generates a random username."""
    characters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(characters) for i in range(length))

def generate_strong_password(length=12):
    """Generates a strong password with letters, numbers, and symbols."""
    characters = string.ascii_letters + string.digits + string.punctuation
    if length < 8:
        length = 8  # Ensure minimum length
    return ''.join(random.choice(characters) for i in range(length))

def save_account_to_json(account_data, filename="mailtm_accounts.json"):
    """Saves account data to a JSON file."""
    accounts = load_accounts_from_json(filename) # Load existing accounts
    accounts.append(account_data) # Add new account
    try:
        with open(filename, 'w') as f:
            json.dump(accounts, f, indent=4)
        print(f"Account saved to {filename}")
    except Exception as e:
        print(f"Error saving account to JSON: {e}")

def load_accounts_from_json(filename="mailtm_accounts.json"):
    """Loads account data from a JSON file."""
    if not os.path.exists(filename):
        return [] # Return empty list if file doesn't exist
    try:
        with open(filename, 'r') as f:
            accounts = json.load(f)
        return accounts
    except FileNotFoundError:
        return [] # Handle case where file is not found (shouldn't happen now but for safety)
    except json.JSONDecodeError:
        print("Warning: JSON file is empty or corrupted. Returning empty account list.")
        return [] # Handle empty or corrupted json file
    except Exception as e:
        print(f"Error loading accounts from JSON: {e}")
        return []

def main():
    mailtm_api = MailTmAPI()
    accounts_filename = "mailtm_accounts.json"

    while True:
        print("\nOptions:")
        print("1. Create a new temporary email account")
        print("2. View and use existing accounts")
        print("3. Exit")
        choice = input("Enter your choice (1/2/3): ")

        if choice == '1':
            # 1. Get available domains
            domains = mailtm_api.get_domains()
            if not domains:
                print("Failed to retrieve domains. Exiting account creation.")
                continue

            print("Available Domains:")
            for i, domain in enumerate(domains):
                print(f"{i+1}. {domain}")

            selected_domain_index = int(input(f"Select a domain (1-{len(domains)}): ")) - 1
            if not 0 <= selected_domain_index < len(domains):
                print("Invalid domain selection.")
                continue
            selected_domain = domains[selected_domain_index]

            # 2. Generate Username and Password
            username = generate_random_username()
            password = generate_strong_password()
            print(f"Generated Username: {username}") # Inform user of generated username
            print("Generated Password (saved securely, not displayed again).")

            # 3. Create Account
            account_data = mailtm_api.create_account(username, password, selected_domain)
            if not account_data:
                print("Account creation failed. Please check errors and try again.")
                continue

            print("\nAccount Created Successfully!")
            print(f"Email Address: {account_data['address']}")
            print(f"Account ID: {account_data['id']}")

            # 4. Save Account to JSON
            save_account_to_json(account_data, accounts_filename)

            token = account_data['token'] # Token available for immediate message check

        elif choice == '2':
            existing_accounts = load_accounts_from_json(accounts_filename)
            if not existing_accounts:
                print("No accounts found in the saved accounts file.")
                continue

            print("\nSaved Accounts:")
            for i, account in enumerate(existing_accounts):
                print(f"{i+1}. {account['address']} (ID: {account['id']})")

            account_index = int(input(f"Select an account to view messages (1-{len(existing_accounts)}): ")) - 1
            if not 0 <= account_index < len(existing_accounts):
                print("Invalid account selection.")
                continue

            selected_account = existing_accounts[account_index]
            token = selected_account['token'] # Load token from saved account data
            print(f"\nUsing account: {selected_account['address']}")

        elif choice == '3':
            print("Exiting.")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")
            continue # Back to options menu

        # Common message retrieval section for both new and existing accounts (if token is available)
        if 'token' in locals() and token: # Check if token is defined
            print("\nChecking for new messages...")
            messages = mailtm_api.get_messages(token)
            if messages is not None:
                if messages:
                    print("\n--- Messages ---")
                    for msg in messages:
                        print(f"Message ID: {msg['id']}")
                        print(f"From: {msg['from']['address']}")
                        print(f"Subject: {msg['subject']}")
                        print(f"Intro: {msg['intro']}")
                        print("-" * 20)

                    if messages:
                        view_message = input("Enter Message ID to view full content (or press Enter to skip): ").strip()
                        if view_message:
                            message_content = mailtm_api.get_message_content(token, view_message)
                            if message_content:
                                print("\n--- Message Content ---")
                                print(f"From: {message_content['from']['address']}")
                                print(f"To: {[to['address'] for to in message_content['to']]}")
                                print(f"Subject: {message_content['subject']}")
                                print(f"Text Body:\n{message_content['text']}")
                                print("-" * 20)
                            else:
                                print("Failed to retrieve full message content.")
                else:
                    print("No messages found in your inbox yet.")
            else:
                print("Failed to retrieve message list.")
            del token # Remove token variable after use in this loop iteration to prevent accidental reuse in next loop if account creation/selection fails.


if __name__ == "__main__":
    main()