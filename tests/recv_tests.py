import imaplib
import os
import ssl
import email
import boto3
import base64
import json
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from botocore.exceptions import ClientError

# Usage: recv_tests.py imap-server-name [region]

# TO DO:
# 1.

# default region. Can be overriden by specifying [region] in arguments
region = "eu-west-1"
imap_port = 993
responder_emails = ["check-auth@verifier.port25.com",
                    "autorespond+dkim@dk.elandsys.com"]


def get_creds(profile, region):

    secret_name = "autotest/" + profile
    print("Getting secret_name: ", secret_name)

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        else:
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
            return secret
        else:
            decoded_binary_secret = base64.b64decode(
                get_secret_value_response['SecretBinary'])
            return decoded_binary_secret


#    imqp_server = "mailhub.mulini.org"
if len(sys.argv) == 1:
    print("Usage: recv_tests.py imap-server-name [region]")
    exit()
else:
    imap_server = sys.argv[1]
    if len(sys.argv) > 2:
        region = sys.argv[2]

creds = json.loads(get_creds(imap_server, region))
#email_address = creds["email"]
imap_server_user = creds["server_username"]
imap_server_password = creds["password"]

# Try to log in to server and get emails
try:
    mail = imaplib.IMAP4_SSL(imap_server, imap_port)
    mail.login(imap_server_user, imap_server_password)
    mail.select('Inbox')
    typ, data = mail.search(None, 'NEW')
    mail_ids = data[0]
    id_list = mail_ids.split()
    print(id_list)

    for num in data[0].split():
        typ, data = mail.fetch(num, '(RFC822)' )
        raw_email = data[0][1]

        for response_part in data:
            if isinstance(response_part, tuple):
                msg = email.message_from_string(response_part[1].decode('utf-8'))
                email_subject = msg['subject']
                email_from = msg['from']
                print('From : ' + email_from)
                print('Subject : ' + email_subject + '\n')
                #print(msg.get_payload(decode=True))

except Exception as e:
    # Print any error messages to stdout
    print(e)
finally:
    mail.close()
    mail.logout()



