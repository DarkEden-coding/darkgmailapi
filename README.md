# Gmail API Python Library
This library provides an easy way to interact with the Gmail API using Python. With this library, you can send emails with attachments, authenticate with the Gmail API, and manage your email accounts.

## Usage
To use this library, you'll need to have a Google API Console project with the Gmail API enabled. You can follow the steps outlined in the Gmail API Quickstart Guide to set up your project.

The library requires the following dependencies:
```
google-api-python-client
google-auth-httplib2
google-auth-oauthlib
```
you can install these dependencies using pip:
```
pip install -r requirements.txt
```
You'll also need to have a credentials.json file for your API project, which you can download from the API Console.

You can use the following code to get started with the Gmail API:
```py
from darkgmailapi import GmailApi

# Create a GmailApi object
gmail = GmailApi(credentials="path/to/credentials.json", send_email="you@example.com", token_file="path/to/token.pickle", scope="https://mail.google.com/")

# Build a message to send
message = gmail.build_message(destination="recipient@example.com",
                               obj="Subject of the email",
                               body="Body of the email")

# Send the message
gmail.send_message("me", message.as_bytes())
```
You can also attach files to your emails using the add_attachment method:
```py
# Add an attachment to the message
gmail.add_attachment(message, "path/to/attachment.pdf")
```
to search for emails, you can use the search method:
```py
# Search for emails
emails = gmail.search("search query")
# returns a list of messages
```
to get the body of an email, you can use the read_message method:
```py
# Read the data of an email
message_data = gmail.read_message(emails[0])
# returns a dictionary with the email data, in this format
# {
#   "from": "",
#   "to": "",
#   "subject": "",
#   "date": "",
#   "body_html": "",
#   "body_text": ""
# }
```
to delete an email, you can use the delete_message method:
```py
# Delete an email
gmail.delete_message(emails[0])
```
to read and unread emails, you can use the mark_as_read and mark_as_unread methods:
```py
# Mark an email as read
gmail.mark_as_read(emails[0])

# Mark an email as unread
gmail.mark_as_unread(emails[0])
```

read more:
  https://www.thepythoncode.com/article/reading-emails-in-python
