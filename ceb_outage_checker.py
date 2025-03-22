import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime, timedelta
import os
import sys

# Config from environment variables
login_url = "https://cebcare.ceb.lk/Identity/Account/Login"
username = os.environ.get("CEB_USERNAME", "")
password = os.environ.get("CEB_PASSWORD", "")
NTFY_URL = os.environ.get("NTFY_URL", "")

# Constants
NOTIFICATION_HISTORY_FILE = "notification_history.json"

def get_csrf_token(response_text):
    """Extract CSRF token from the login page"""
    soup = BeautifulSoup(response_text, 'html.parser')
    token = soup.find('input', {'name': '__RequestVerificationToken'})
    if token:
        return token.get('value')
    return None

def send_ntfy_notification(title, message, priority="default", tags=None):
    """Send notification via ntfy.sh"""
    headers = {
        "Title": title,
        "Priority": priority,
        "Content-Type": "text/plain; charset=utf-8"
    }
    
    if tags:
        headers["Tags"] = tags
    
    try:
        # Use direct string data instead of encoding it ourselves
        response = requests.post(
            NTFY_URL, 
            data=message,  # Let requests handle the encoding
            headers=headers
        )
        
        if response.status_code == 200:
            print(f"Notification sent successfully: {title}")
            return True
        else:
            print(f"Failed to send notification: {response.status_code}, {response.text}")
            return False
    except Exception as e:
        print(f"Error sending notification: {str(e)}")
        return False

def load_notification_history():
    """Load previously sent notification IDs"""
    if os.path.exists(NOTIFICATION_HISTORY_FILE):
        try:
            with open(NOTIFICATION_HISTORY_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading notification history: {str(e)}")
            return {"notified_outages": []}
    else:
        return {"notified_outages": []}

def save_notification_history(history):
    """Save notification history"""
    try:
        with open(NOTIFICATION_HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving notification history: {str(e)}")
        return False

def create_outage_id(outage):
    """Create a unique identifier for an outage"""
    return f"{outage['startTime']}|{outage['endTime']}|{outage['description']}"

def login_and_fetch_outages(force_tomorrow_notifications=False):
    """Perform login and fetch outage data"""
    # Create a session to maintain cookies
    session = requests.Session()
    
    # First, get the login page to extract the CSRF token
    print("Fetching login page...")
    response = session.get(login_url)
    
    if response.status_code != 200:
        print(f"Failed to access login page: {response.status_code}")
        return None
    
    # Extract CSRF token
    csrf_token = get_csrf_token(response.text)
    if not csrf_token:
        print("Failed to extract CSRF token")
        return None
    
    # Prepare login payload
    payload = {
        "Input.UserName": username,
        "Input.Password": password,
        "__RequestVerificationToken": csrf_token,
        "Input.RememberMe": "false"
    }
    
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "en-US,en;q=0.9,si;q=0.8,eo;q=0.7",
        "cache-control": "no-cache",
        "content-type": "application/x-www-form-urlencoded",
        "pragma": "no-cache",
        "sec-ch-ua": "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Google Chrome\";v=\"134\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1"
    }
    
    # Perform login
    print("Attempting login...")
    login_response = session.post(login_url, data=payload, headers=headers, allow_redirects=True)
    
    # Check if login was successful
    if login_response.status_code == 200:
        print("Login successful!")
        accounts = [
            {'AcctNo': '4603310609', 'AcctName': 'A7'},
            {'AcctNo': '4604009007', 'AcctName': 'A8'},
            {'AcctNo': '4612288009', 'AcctName': 'A48'}
        ]
        
        # Dictionary to track unique outages by time and description
        unique_outages = {}
        
        for account in accounts:
            acct_no = account['AcctNo']
            acct_name = account['AcctName']
            
            print(f"Fetching outages for account: {acct_no} ({acct_name})")
            
            # Calculate date range (current month)
            today = datetime.now()
            start_date = today.strftime('%Y-%m-%d')
            end_date = (today + timedelta(days=30)).strftime('%Y-%m-%d')
            
            # Fetch calendar data
            calendar_url = f"https://cebcare.ceb.lk/Outage/GetCalendarData?from={start_date}&to={end_date}&acctNo={acct_no}"
            
            outage_response = session.get(calendar_url)
            if outage_response.status_code == 200:
                outage_data = json.loads(outage_response.text)
                
                # Process each outage
                for outage in outage_data.get('interruptions', []):
                    # Create a unique key based on start time, end time, and description
                    key = f"{outage['startTime']}|{outage['endTime']}|{outage['description']}"
                    
                    if key not in unique_outages:
                        # First time seeing this outage
                        outage['accounts'] = [{'number': acct_no, 'name': acct_name}]
                        unique_outages[key] = outage
                    else:
                        # Already seen this outage, just add this account to the list
                        unique_outages[key]['accounts'].append({'number': acct_no, 'name': acct_name})
        
        # Convert back to list
        consolidated_outages = list(unique_outages.values())
        
        # Save all consolidated outages to a file
        with open('ceb_outages.json', 'w') as f:
            json.dump(consolidated_outages, f, indent=4)
        
        # Load notification history
        notification_history = load_notification_history()
        notified_outages = notification_history['notified_outages']
        new_notifications = []
        
        # Tomorrow's date
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        
        # Process and send notifications
        print("\nProcessing outages for notifications:")
        for outage in consolidated_outages:
            start_time = datetime.fromisoformat(outage['startTime'].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(outage['endTime'].replace('Z', '+00:00'))
            
            # Move account_list creation outside the notification condition
            account_list = ", ".join([f"{acc['name']} ({acc['number']})" for acc in outage['accounts']])
            
            # Check if this outage is tomorrow
            is_tomorrow = start_time.date() == tomorrow or end_time.date() == tomorrow
            
            # Create outage ID for tracking
            outage_id = create_outage_id(outage)
            
            # Determine if we should send notification
            should_notify = (outage_id not in notified_outages) or (is_tomorrow and force_tomorrow_notifications)
            
            if should_notify:
                # Prepare notification title and message
                title = "CEB Power Outage"
                if is_tomorrow:
                    title = "TOMORROW'S POWER OUTAGE!"
                
                message = (
                    f"Type: {outage['interruptionTypeName']}\n"
                    f"Affected Accounts: {account_list}\n"
                    f"Description: {outage['description']}\n"
                    f"From: {start_time.strftime('%Y-%m-%d %H:%M')}\n"
                    f"To: {end_time.strftime('%Y-%m-%d %H:%M')}\n"
                    f"Status: {outage.get('status', 'N/A')}"
                )
                
                # Set priority based on timing
                priority = "default"
                tags = "warning"
                if is_tomorrow:
                    priority = "high"
                    tags = "warning,calendar,alert"
                
                # Send notification
                if send_ntfy_notification(title, message, priority, tags):
                    # Add to history only if it's a new notification (not forced)
                    if outage_id not in notified_outages:
                        notified_outages.append(outage_id)
                        new_notifications.append({
                            "id": outage_id,
                            "sent_at": datetime.now().isoformat(),
                            "is_tomorrow": is_tomorrow
                        })
            
            # Always print outage info in console
            print(f"Outage: {start_time.strftime('%Y-%m-%d')} to {end_time.strftime('%Y-%m-%d')}")
            print(f"   Accounts: {account_list}")
            print(f"   Notification status: {'Sent' if should_notify else 'Already notified'}")
            
        # Save updated notification history
        notification_history['notified_outages'] = notified_outages
        save_notification_history(notification_history)
        
        # Send summary notification if any new notifications were sent
        if new_notifications:
            summary = f"Found {len(new_notifications)} new outage(s)"
            send_ntfy_notification("CEB Outage Summary", summary, "low", "info")
        else:
            print("No new outages to notify about.")
        
        return consolidated_outages
    else:
        print("Login failed!")
        error_msg = "Failed to log in to CEB Care. Please check credentials."
        send_ntfy_notification("CEB Script Error", error_msg, "high", "warning")
        return None

# Main execution
if __name__ == "__main__":
    print("Starting CEB outage data extraction...")
    # Always check for tomorrow's outages when running in GitHub Actions
    outages = login_and_fetch_outages(force_tomorrow_notifications=True)
