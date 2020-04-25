import smtplib, ssl, email, boto3, base64, json, sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from botocore.exceptions import ClientError

# Usage: send_tests.py smtp-server-name [region]

# TO DO:
# 1. Determine which domain to test
# 3. More error handling & reporting?

region = "eu-west-1" # default region. Can be overriden by specifying [region] in arguments
port = 25
receiver_email = "check-auth@verifier.port25.com, autorespond+dkim@dk.elandsys.com"
message = """\

Please test this."""

def get_creds(profile, region):

    secret_name = "autotest/" + profile
    print("Getting secret_name: ", secret_name)
    # region_name = "eu-west-1"

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
            decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
            return decoded_binary_secret



#    smtp_server = "mailhub.mulini.org" # Eventually to be passed as an arguement to determine params to be used
if len(sys.argv) == 1:
    print( "Usage: send_tests.py smtp-server-name [region]" )
    exit()
else:
    smtp_server = sys.argv[1]
    if len(sys.argv) > 2:
        region = sys.argv[2]

creds = json.loads( get_creds(smtp_server, region) )
sender_email = creds["email"]
smtp_server_user = creds["server_username"]
smtp_server_password = creds["password"]

msg = MIMEMultipart()
msg['From'] = sender_email
msg['To'] = receiver_email
msg['Subject'] = "Test"
msg['Date'] = datetime.now().astimezone().strftime("%a, %d %b %Y %H:%M:%S %z")
msg.attach(MIMEText(message,'plain'))

context = ssl.create_default_context()

# Try to log in to server and send email
try:
    server = smtplib.SMTP(smtp_server,port)
    server.ehlo() # Can be omitted
    server.starttls(context=context) # Secure the connection
    server.ehlo() # Can be omitted
    server.login(smtp_server_user, smtp_server_password)
    server.send_message(msg)
    print("Test messages sent successfully to SMTP relay")
except Exception as e:
    # Print any error messages to stdout
    print(e)
finally:
    server.quit() 

