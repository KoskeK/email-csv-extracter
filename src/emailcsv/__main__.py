import imaplib
import email
from email.policy import default
import csv
import os
import json

with open('config.json', 'r') as j:
    CONFIG = json.load(j)
CSV_FILENAME = "emails_dump.csv"

def get_email_body(msg):
    """Extracts the plain text body from an email message."""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            
            # Look for plain text and ignore attachments
            if content_type == "text/plain" and "attachment" not in content_disposition:
                try:
                    body = part.get_payload(decode=True).decode(part.get_content_charset('utf-8'), errors='ignore')
                except Exception:
                    pass
                break # Stop after finding the first plain text part
    else:
        # Not multipart, just a standard text email
        if msg.get_content_type() == "text/plain":
            try:
                body = msg.get_payload(decode=True).decode(msg.get_content_charset('utf-8'), errors='ignore')
            except Exception:
                pass
                
    return body.strip()

def download_emails_to_csv(IMAP_SERVER, EMAIL_ACCOUNT, PASSWORD, MAILBOX):
    print(f"Connecting to {IMAP_SERVER}...")
    
    try:
        # 1. Connect to the server
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ACCOUNT, PASSWORD)
        print("Login successful.")

        # 2. Select the mailbox
        status, messages = mail.select(MAILBOX)
        if status != 'OK':
            print(f"Failed to select mailbox: {MAILBOX}")
            return

        # 3. Search for all emails
        print("Searching for emails...")
        status, data = mail.search(None, 'ALL')
        
        # Data is a list containing a space-separated string of email IDs
        email_ids = data[0].split()
        total_emails = len(email_ids)
        print(f"Found {total_emails} emails. Starting download...")

        # 4. Open CSV for writing
        with open(CSV_FILENAME, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Write the header row
            writer.writerow(["Message ID", "Date", "From", "To", "Subject", "Body"])

            # Loop through IDs in reverse to get newest first (optional)
            for i, e_id in enumerate(reversed(email_ids)):
                print(f"Processing email {i+1}/{total_emails}...", end='\r')
                
                # Fetch the raw email data
                status, msg_data = mail.fetch(e_id, '(RFC822)')
                
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        # Parse the bytes into an email object
                        msg = email.message_from_bytes(response_part[1], policy=default)
                        
                        # Extract basic metadata
                        msg_id = msg.get("Message-ID", "")
                        date = msg.get("Date", "")
                        sender = msg.get("From", "")
                        recipient = msg.get("To", "")
                        subject = msg.get("Subject", "")
                        
                        # Extract body
                        body = get_email_body(msg)
                        
                        # Write to CSV
                        writer.writerow([msg_id, date, sender, recipient, subject, body])
                        
        print(f"\nSuccess! Exported {total_emails} emails to {CSV_FILENAME}")

    except imaplib.IMAP4.error as e:
        print(f"IMAP Error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Clean up the connection
        try:
            mail.close()
            mail.logout()
        except:
            pass

if __name__ == "__main__":
    download_emails_to_csv()