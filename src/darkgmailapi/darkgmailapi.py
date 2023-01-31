import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from base64 import urlsafe_b64decode, urlsafe_b64encode
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from mimetypes import guess_type as guess_mime_type


# make init class for GmailApi, makes vars for scope, send_email, credentials
class GmailApi:

    def __init__(self, scope=None, send_email=None, credentials="credentials.json", token_file="token.pickle"):
        """
        makes a GmailApi object
        :param scope: the scope of the Gmail API (e.g. ["https://mail.google.com/"])
        :param send_email: your email address
        :param credentials: path to your credentials.json file
        :param token_file: path to your token.pickle file
        """
        if scope is None:
            scope = ["https://mail.google.com/"]
        self.scopes = scope
        self.send_email = send_email
        self.credentials = credentials
        self.token_file = token_file
        self.service = self.gmail_authenticate()

    def gmail_authenticate(self):
        """
        Authenticate with Gmail API
        :return: authenticated Gmail API service
        """
        creds = None
        # the file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time
        if os.path.exists(self.token_file):
            with open(self.token_file, "rb") as token:
                creds = pickle.load(token)
        # if there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials, self.scopes)
                creds = flow.run_local_server(port=0)
            # save the credentials for the next run
            with open(self.token_file, "wb") as token:
                pickle.dump(creds, token)
        return build('gmail', 'v1', credentials=creds)

    # Adds the attachment with the given filename to the given message
    def add_attachment(self, message, filename):
        """
        Adds the attachment with the given filename to the given message
        :param message: message to attach to
        :param filename: filename of the attachment
        :return:
        """
        content_type, encoding = guess_mime_type(filename)
        if content_type is None or encoding is not None:
            content_type = 'application/octet-stream'
        main_type, sub_type = content_type.split('/', 1)
        if main_type == 'text':
            fp = open(filename, 'rb')
            msg = MIMEText(fp.read().decode(), _subtype=sub_type)
            fp.close()
        elif main_type == 'image':
            fp = open(filename, 'rb')
            msg = MIMEImage(fp.read(), _subtype=sub_type)
            fp.close()
        elif main_type == 'audio':
            fp = open(filename, 'rb')
            msg = MIMEAudio(fp.read(), _subtype=sub_type)
            fp.close()
        else:
            fp = open(filename, 'rb')
            msg = MIMEBase(main_type, sub_type)
            msg.set_payload(fp.read())
            fp.close()
        filename = os.path.basename(filename)
        msg.add_header('Content-Disposition', 'attachment', filename=filename)
        message.attach(msg)

    def build_message(self, destination, obj, body, attachments=None):
        """
        Builds the message to send
        :param destination: destination email address
        :param obj: subject of the email
        :param body: body of the email
        :param attachments: attachments to add to the email
        :return:
        """
        if attachments is None:
            attachments = []
        if not attachments:  # no attachments given
            message = MIMEText(body)
            message['to'] = destination
            message['from'] = self.send_email
            message['subject'] = obj
        else:
            message = MIMEMultipart()
            message['to'] = destination
            message['from'] = self.send_email
            message['subject'] = obj
            message.attach(MIMEText(body))
            for filename in attachments:
                self.add_attachment(message, filename)
        return {'raw': urlsafe_b64encode(message.as_bytes()).decode()}

    def send_message(self, destination, obj, body, attachments=None):
        """
        Sends the message
        :param destination: destination email address
        :param obj: subject of the email
        :param body: body of the email
        :param attachments: attachments to add to the email
        :return: api response
        """
        if attachments is None:
            attachments = []
        return self.service.users().messages().send(
            userId="me",
            body=self.build_message(destination, obj, body, attachments)
        ).execute()

    def search_messages(self, query):
        """
        Search for messages matching the query
        :param query: query to search for
        :return: list of messages
        """
        result = self.service.users().messages().list(userId='me', q=query).execute()
        messages = []
        if 'messages' in result:
            messages.extend(result['messages'])
        while 'nextPageToken' in result:
            page_token = result['nextPageToken']
            result = self.service.users().messages().list(userId='me', q=query, pageToken=page_token).execute()
            if 'messages' in result:
                messages.extend(result['messages'])
        return messages

    def get_data_from_part(self, part, print_data=False, save_attachments=False, attachment_dir=None,
                           message_data=None):
        filename = part.get("filename")
        mimeType = part.get("mimeType")
        body = part.get("body")
        data = body.get("data")
        if print_data:
            print("mime type: " + mimeType)

        if mimeType == "text/plain":
            # we print the text/plain part of the message
            if print_data:
                print(f"Text: {urlsafe_b64decode(data).decode()}")
            message_data['body_text'] = urlsafe_b64decode(data).decode()
        elif mimeType == "text/html":
            # we print the text/html part of the message
            if print_data:
                print(f"Html: {urlsafe_b64decode(data).decode()}")
            message_data['body_html'] = urlsafe_b64decode(data).decode()

        # attachments
        if filename:
            if print_data:
                print(f"Attachment: {filename}")
            if save_attachments:
                if not attachment_dir:
                    attachment_dir = os.path.join(os.getcwd(), "attachments")
                if not os.path.exists(attachment_dir):
                    os.mkdir(attachment_dir)
                file_path = os.path.join(attachment_dir, filename)
                if not os.path.isfile(file_path):
                    with open(file_path, 'wb') as f:
                        f.write(urlsafe_b64decode(data))
                else:
                    print("File already exists")

        return message_data

    def read_message(self, message, save_attachments=False, attachment_dir=None, print_data=False):
        """
        Read an email message and returns it as a dictionary
        :param message: message to read
        :param save_attachments: if True, attachments will be saved in the attachment_dir
        :param attachment_dir: directory where attachments will be saved
        :param print_data: if True, the message data will be printed
        :return: message data
        """
        msg = self.service.users().messages().get(userId='me', id=message['id'], format='full').execute()
        # parts can be the message body, or attachments

        message_data = {'from': '', 'to': '', 'subject': '', 'date': '', 'body_html': '', 'body_text': ''}
        payload = msg['payload']
        headers = payload.get("headers")
        if headers:
            # this section prints email basic info & creates a folder for the email
            for header in headers:
                name = header.get("name")
                value = header.get("value")
                if name.lower() == 'from':
                    # we print the From address
                    if print_data:
                        print("From:", value)
                    message_data['from'] = value
                if name.lower() == "to":
                    # we print the To address
                    if print_data:
                        print("To:", value)
                    message_data['to'] = value
                if name.lower() == "subject":
                    if print_data:
                        print("Subject:", value)
                    message_data['subject'] = value
                if name.lower() == "date":
                    # we print the date when the message was sent
                    if print_data:
                        print("Date:", value)
                    message_data['date'] = value

        # gets the message body and attachments using the get_data_from_part function, supports multiple parts
        parts = payload.get("parts")
        if parts:
            for part in parts:
                # sees if the part is an attachment
                if part.get("filename"):
                    # gets the attachment data
                    self.get_data_from_part(part, print_data, save_attachments, attachment_dir, message_data)
                # sees if the part is the message body
                elif part.get("mimeType") == "text/plain" or part.get("mimeType") == "text/html":
                    # gets the message body data
                    message_data = self.get_data_from_part(part, print_data, save_attachments, attachment_dir,
                                                           message_data)
                # sees if the part is multipart/alternative
                elif part.get("mimeType") == "multipart/alternative":
                    # loops through the parts of the multipart/alternative part
                    for part2 in part.get("parts"):
                        # gets the message body data
                        message_data = self.get_data_from_part(part2, print_data, save_attachments, attachment_dir,
                                                               message_data)
        else:
            # gets the message body data
            message_data = self.get_data_from_part(payload, print_data, save_attachments, attachment_dir, message_data)

        if print_data:
            print("=" * 50)

        return message_data

    def mark_as_read(self, msg):
        """
        Mark a single message as read
        :param msg: message to mark as read
        :return: api response
        """
        # mark a single message as read
        return self.service.users().messages().modify(
            userId='me',
            id=msg['id'],
            body={
                'removeLabelIds': ['UNREAD'],
            }
        ).execute()

    def mark_as_unread(self, msg):
        """
        Mark a single message as unread
        :param msg: message to mark as unread
        :return: api response
        """
        # mark a single message as unread
        return self.service.users().messages().modify(
            userId='me',
            id=msg['id'],
            body={
                'addLabelIds': ['UNREAD'],
            }
        ).execute()

    def delete_messages(self, msg):
        """
        Delete a single message
        :param msg: message to delete
        :return: api response
        """
        # delete a single message
        return self.service.users().messages().delete(
            userId='me',
            id=msg['id']
        ).execute()
