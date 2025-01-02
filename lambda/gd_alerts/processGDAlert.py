import json
import sys
import logging
import boto3
from dynamodb_nacl import DynamodbBlocklist

sns_topic_arn = "arn:aws:sns:eu-west-1:432173269038:GuardDuty_alerts" # TO DO: ENV variable
nacl_id = "acl-07116746e62b32a9d"                                     # TO DO: ENV variable
table_name = "gdBlockNACL_" + nacl_id

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def lambda_handler(event, context):
    # parsed = json.load(event)
    # print(json.dumps(event, indent=4, sort_keys=True))

    # Determine what kind of alert we have
    try:
        # is actionType key present?
        action = event['detail']['service']['action']['actionType']
    except:
        # actionType not in event JSON, quit
        logging.error("actionType element not found in Guard Duty event")
        return False

    if action == "PORT_PROBE":
        #print("Action is PORT_PROBE")
        return (dealwith_portprobe(event))
        
    # other actionTypes can go here...
    else:
        # just send the raw message:
        client = boto3.client('sns')
        response = client.publish(
            TopicArn = sns_topic_arn,
            Subject = 'Guard Duty Alert',
            Message = json.dumps(event, indent=4)
        )
        return response

def dealwith_portprobe(event):
    # Publishes message with summary details to sns_topic_arn and
    # populates list of bad remote IPs that are probing us, so we can do something about it (to do)
    # Need to get:
    #  name from detail->resource->instanceDetails->tags->[value where key==Name]
    #  count from detail->service->count
    #  firstseen from detail->service->eventFirstSeen
    #  badguys from detail->service->action->portProbeAction->portProbeDetails[]
    
    for tags in event['detail']['resource']['instanceDetails']['tags']:
        if tags['key'] == 'Name':
            name = tags['value']

    try:
        name
    except NameError:
        name = event['detail']['resource']['instanceDetails']['instanceId']
    
    count = str(int(event['detail']['service']['count']))
    firstseen = event['detail']['service']['eventFirstSeen']
    badguys = event['detail']['service']['action']['portProbeAction']['portProbeDetails']
    badguysIPs = []

    message = "Name: "+name+"\nCount: "+count+"\nFirst Seen: "+firstseen+"\nNumber of bad guys: "+str(len(badguys))
    message += "\n----------"
    for badguy in badguys:
        message += "\nRemote IP: "+badguy['remoteIpDetails']['ipAddressV4']
        message += "\n  Organisation: "+badguy['remoteIpDetails']['organization']['org']
        message += "\n  City: "+badguy['remoteIpDetails']['city']['cityName']
        message += "\n  Country: "+badguy['remoteIpDetails']['country']['countryName']
        message += "\n  Local service probed: "+ str(int(badguy['localPortDetails']['port']))+" ("+badguy['localPortDetails']['portName']+")"
        badguysIPs.append(badguy['remoteIpDetails']['ipAddressV4'])

        message +="\n *** "+add_to_block_NACL(badguy['remoteIpDetails']['ipAddressV4'])+" ***"

    # print(message)
    # send SNS message:
    client = boto3.client('sns')
    response = client.publish(
        TopicArn = sns_topic_arn,
        Subject = 'Guard Duty Alert: '+name+' is being probed on an open port by a known malicious IP',
        Message = message
    )


    return response

def add_to_block_NACL(ipAddress):
    # Get gdBlockCounter from nacl_state
    # For entry nacl_rule_<gdBlockCounter>, add ipAddress to cidrBlock field; add date to dateBlocked field
    # increment gdBlockCounter in nacl_state.  If gdBlockCounter = gdBlockEndAt, then gdBlockCounter = gdBlockStartAt

    # 1) Check table exists and load it 
    myTable = DynamodbBlocklist(boto3.resource('dynamodb'))
    myTable_name = 'blockNACL_'+nacl_id
    myTable_exists = myTable.exists(myTable_name)
    if not myTable_exists:
        logger.info("Creating table %s ...", myTable_name)
        myTable.create_table(nacl_id, 30, 1, 38)
        logger.info("Created table %s.", myTable_name)
    else:
        logger.info("Table %s already exists", myTable_name)

    # 2) Attempt to block itpr
    return myTable.add_cidr(ipAddress, 32)



 
 
"""
    try:
        table = resource.Table(table_name)
        table.load()
    except ClientError as err:
        if err.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"Table name {table_name} not found")
        else:
            print(f"Couldn't check for existence of {table_name}. Here's why: {err.response['Error']['Code']}: {err.response['Error']['Message']}")
        raise

    cidrSearch = ipAddress+'/32'

    # 2) Search table for existing entry for cidrSearch
    try:
        response = table.scan(FilterExpression = Attr('cidrBlock').eq(cidrSearch))
        #print(response["Count"])
    except ClientError as err:
        print(f"Couldn't scan {table_name}.  Here's why: {err.response['Error']['Code']}: {err.response['Error']['Message']}")
        raise

    if response["Count"] > 0:
        return f"{ipAddress} already in Guard Duty blocklist"

    # 3) Get nacl_state entry
    try:
        response = table.get_item(Key={'nacl_id': 'acl-07116746e62b32a9d', 'nacl_entry': 'nacl_state'})
    except ClientError as err:
        print(f"Couldn't get nacl_entry from {table_name}.  Here's why: {err.response['Error']['Code']}: {err.response['Error']['Message']}")
        raise

    gdBlockCounter = response['Item']['gdBlockCounter']
    gdBlockEndAt = response['Item']['gdBlockEndAt']
    gdBlockStartAt = response['Item']['gdBlockStartAt']

    # 4) Create table entry:
    new_entry = {
        'nacl_id': 'acl-07116746e62b32a9d',
        'nacl_entry': f'nacl_rule_{gdBlockCounter}',
        'cidrBlock': f'{ipAddress}/32',
        'dateBlocked': f'{time.time()}'
    }
    #print(json.dumps(new_entry, indent=4))

    # 5) Add entry:
    try:
        table.put_item(Item=new_entry)
    except ClientError as err:
        print(f"Couldn't add new NACL item to DynamoDB table.  Here's why: {err.response['Error']['Code']}: {err.response['Error']['Message']}")
        raise

    # Actually block the IP:
    ec2Resource = boto3.client("ec2")

    # 6) Delete NACL rule number if it already exists
    try:
        # Just try and delete it, but carry on if delete doesn't work as rule may not be present
        response = ec2Resource.delete_network_acl_entry(
            Egress=False,
            NetworkAclId='acl-07116746e62b32a9d',
            RuleNumber=int(gdBlockCounter)
        )
    except ClientError as err:
        print(f"Couldn't delete NACL rule {gdBlockCounter}.  Here's why: {err.response['Error']['Code']}: {err.response['Error']['Message']}")
    else:
        print(f"NACL rule {gdBlockCounter} deleted to make way for new rule")

    # 7) Add new NACL entry
    try:
        response = ec2Resource.create_network_acl_entry(
            CidrBlock=f'{ipAddress}/32',
            Egress=False,
            NetworkAclId='acl-07116746e62b32a9d', # Need to fix this
            Protocol='-1',
            RuleAction='deny',
            RuleNumber=int(gdBlockCounter)
        )
    except ClientError as err:
        print(f"Couldn't add new rule to NACL.  Here's why: {err.response['Error']['Code']}: {err.response['Error']['Message']}")
        raise

    gdBlockCounter += 1
    if gdBlockCounter == gdBlockEndAt:
        gdBlockCounter = gdBlockStartAt
    
    # 8) Write new nacl_state entry:
    try:
        response = table.update_item(Key={'nacl_id': 'acl-07116746e62b32a9d', 'nacl_entry': 'nacl_state'},
            UpdateExpression = "set gdBlockCounter=:g",
            ExpressionAttributeValues = {':g': gdBlockCounter},
            ReturnValues="UPDATED_NEW"
        )
    except ClientError as err:
        print(f"Couldn't update nacl_state entry.  Here's why: {err.response['Error']['Code']}: {err.response['Error']['Message']}")
        raise
    
    #print(response['Attributes'])

    return f"{ipAddress} added to Guard Duty blocklist"
"""

if __name__ == "__main__":
    testEvent = json.loads(sys.stdin.read())
    # print(json.dumps(myEvent, indent=4))
    lambda_handler(testEvent,"NO_CONTEXT")
