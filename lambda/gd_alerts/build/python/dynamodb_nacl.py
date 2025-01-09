import time
import logging
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Attr

logger = logging.getLogger(__name__)

class DynamodbBlocklist:
    """
    Encapsulates a DynamoDB table of Network ACL 'deny' entries that are also replicated within an actual VPC NACL
    Used to continually update and manage a blocklist of source IPs for security purposes
    """
    
    def __init__(self, dyn_resource) -> None:
        """
        :param dyn_resource: A Boto3 DynamoDB resource.
        """
        self.dyn_resource = dyn_resource
        self.table = None
        self.table_name = None

    def exists(self, table_name):
        """
        Determines whether a table exists. As a side effect, stores the table in
        a member variable.

        :param table_name: The name of the table to check.
        :return: True when the table exists; otherwise, False.
        """
        try:
            table = self.dyn_resource.Table(table_name)
            table.load()
            exists = True
        except ClientError as err:
            if err.response['Error']['Code'] == 'ResourceNotFoundException':
                exists = False
            else:
                logger.error(
                    "Couldn't check for existence of %s. Here's why: %s: %s",
                    table_name,
                    err.response['Error']['Code'], err.response['Error']['Message'])
                raise
        else:
            self.table = table
            self.table_name = table_name
        return exists

    def create_table(self, nacl_id, block_age_days, rule_start, rule_end):
        """
        Creates a DynamoDB table for the Network ACL blocklist
        
        :param nacl_id: ID of the AWS NACL that this table will drive
        :param block_age_days: Days a block rule should remain in the NACL
        :param rule_start: Sequence number of first block rule in NACL
        :param rule_end: Sequence number of final block rule in NACL.
                         Remembering that normal NACL limit is 20 and AWS will only raise it to 40
                         And you'll need two entries for a final allow and then the implicit deny all
        :return: The newly created table.
        """
        try:
            self.table = self.dyn_resource.create_table(
                TableName='blockNACL_'+nacl_id,
                KeySchema=[
                    {'AttributeName': 'nacl_id', 'KeyType': 'HASH'},  # Partition key
                    {'AttributeName': 'nacl_entry', 'KeyType': 'RANGE'}  # Sort key
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'nacl_id', 'AttributeType': 'S'},
                    {'AttributeName': 'nacl_entry', 'AttributeType': 'S'}
                ],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5})
            self.table.wait_until_exists()
        except ClientError as err:
            logger.error(
                "Couldn't create table %s. Here's why: %s: %s", 'blockNACL_'+nacl_id,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        
        # Add initial nacl_state entry
        new_entry = {
        'nacl_id': nacl_id,
        'nacl_entry': 'nacl_state',
        'blockAgeInDays': block_age_days,
        'blockStartAt': rule_start,
        'blockEndAt': rule_end,
        'blockCounter': rule_start
        }
        #print(json.dumps(new_entry, indent=4))

        # Add entry:
        try:
            self.table.put_item(Item=new_entry)
        except ClientError as err:
            logger.error(
                "Couldn't add new NACL item to DynamoDB table.  Here's why: %s: %s", 
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise

        return self.table

    def add_cidr(self, ip_address, netmask):
        """
        Add CIDR block to the next available rule in the table,
        but only after checking it's not there already

        :param ip_address: start of CIDR block
        :param netmask: CIDR block mask

        :return: Not sure yet
        """
        
        cidrSearch = ip_address+"/"+str(netmask)

        try:
            response = self.table.scan(FilterExpression = Attr('cidrBlock').eq(cidrSearch))
            #print(response["Count"])
        except ClientError as err:
            logger.error(
                "Couldn't scan %s.  Here's why: %s: %s",
                self.table_name, err.response['Error']['Code'], err.response['Error']['Message'])
            raise

        if response["Count"] > 0:
            return f"{ip_address} already covered by blocklist"


        naclState = self.get_nacl_state()
        naclId = naclState['nacl_id']
        blockCounter = naclState['blockCounter']

        # Create table entry:
        new_entry = {
            'nacl_id': naclId,
            'nacl_entry': f'nacl_rule_{blockCounter}',
            'cidrBlock': f'{ip_address}/{netmask}',
            'dateBlocked': f'{time.time()}'
        }
        #print(json.dumps(new_entry, indent=4))

        # Add entry:
        try:
            self.table.put_item(Item=new_entry)
        except ClientError as err:
            logger.error(
                "Couldn't add new NACL item to DynamoDB table.  Here's why: %s: %s",
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            self.block_cidr(naclId, ip_address, netmask)
            self.increment_nacl_state()
            return f"{ip_address} added to blocklist"


    def get_nacl_state(self):
        """
        Get nacl_state entry

        :return: dict of nacl_state entry
        """
        try:
            #response = self.table.get_item(Key={'nacl_id': 'acl-07116746e62b32a9d', 'nacl_entry': 'nacl_state'})
            response = self.table.scan(FilterExpression = Attr('nacl_entry').eq('nacl_state'))
        except ClientError as err:
            logger.error(
                "Couldn't get nacl_entry from %s.  Here's why: %s: %s",
                self.table_name, err.response['Error']['Code'], err.response['Error']['Message'])
            raise

        return response['Items'][0]
    
    def increment_nacl_state(self):
        """
        Increments (and rolls over if necessary) blockCounter filed in nacl_state entry
        """

        naclState = self.get_nacl_state()

        blockCounter = naclState['blockCounter']
        blockCounter += 1
        if blockCounter == naclState['blockEndAt']:
            blockCounter = naclState['blockStartAt']
        
        # Write new nacl_state entry:
        try:
            response = self.table.update_item(Key={'nacl_id': naclState['nacl_id'], 'nacl_entry': 'nacl_state'},
                UpdateExpression = "set blockCounter=:g",
                ExpressionAttributeValues = {':g': blockCounter},
                ReturnValues="UPDATED_NEW"
            )
        except ClientError as err:
            logger.error(
                "Couldn't update nacl_state entry.  Here's why: %s: %s",
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            return response        

    def block_cidr(self, nacl_id, ip_address, netmask):
        """
        Actually blocks the CIDR in the NACL and updates the nacl_state entry in the table

        :param nacl_id: ID of the NACL to apply rule to
        :param ip_address: start of CIDR block
        :param netmask: CIDR block mask

        :return: string with info on added CIDR
        """
        ec2Resource = boto3.client("ec2")
        blockCounter = int(self.get_nacl_state()['blockCounter'])
        # Delete NACL rule number if it already exists
        try:
            # Just try and delete it, but carry on if delete doesn't work as rule may not be present
            response = ec2Resource.delete_network_acl_entry(
                Egress=False,
                NetworkAclId=nacl_id,
                RuleNumber=blockCounter
            )
        except ClientError as err:
            logger.error(
                "Couldn't delete NACL rule %s.  Here's why: %s: %s",
                blockCounter, err.response['Error']['Code'], err.response['Error']['Message'])
        else:
            logger.info("NACL rule %s deleted to make way for new rule", blockCounter)

        # Add new NACL entry
        try:
            response = ec2Resource.create_network_acl_entry(
                CidrBlock=f'{ip_address}/{netmask}',
                Egress=False,
                NetworkAclId=nacl_id,
                Protocol='-1',
                RuleAction='deny',
                RuleNumber=blockCounter
            )
        except ClientError as err:
            logger.error(
                "Couldn't add new rule to NACL.  Here's why: %s: %s",
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise

        return f"{ip_address}/{netmask} added to Guard Duty blocklist"

    def reset_table(self):
        """
        Clears out all block rules added by the methods here and resets counter
        """

        naclState = self.get_nacl_state()
        try:
            # Get all `nacl_rule_n` entries:
            response = self.table.scan(FilterExpression = Attr('nacl_entry').begins_with('nacl_rule_'))
        except ClientError as err:
            logger.error("Couldn't get list of all nacl rules to delete.  Here's why: %s: %s",
            err.response['Error']['Code'], err.response['Error']['Message'])
            return False

        for rule in response['Items']:
            try:
                del_response = self.table.delete_item(Key={'nacl_id': rule['nacl_id'], 'nacl_entry': rule['nacl_entry']})
            except ClientError as err:
                logging.error("Cloudn't delete item %s.  Here's why: %s: %s",
                rule['nacl_entry'], err.response['Error']['Code'], err.response['Error']['Message'])
                raise

        try:
            response = self.table.update_item(Key={'nacl_id': naclState['nacl_id'], 'nacl_entry': 'nacl_state'},
                UpdateExpression = "set blockCounter=:g",
                ExpressionAttributeValues = {':g': naclState['blockStartAt']},
                ReturnValues="UPDATED_NEW"
            )
        except ClientError as err:
            logger.error(
                "Couldn't update nacl_state entry.  Here's why: %s: %s",
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise

        return True

    def realign_nacl(self):
        """
        Rebuild NACL from entries in table
        """
        pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    myTable = DynamodbBlocklist(boto3.resource('dynamodb'))
    myTable_name = 'blockNACL_acl-07116746e62b32a9d'
    myTable_exists = myTable.exists(myTable_name)
    if not myTable_exists:
        print(f"\nCreating table {myTable_name}...")
        myTable.create_table('acl-07116746e62b32a9d', 30, 1, 38)
        print(f"\nCreated table {myTable_name}.")
    else:
        print("Table exists.")
    print(myTable.add_cidr("1.2.3.4",32))
    print(myTable.add_cidr("5.6.7.8",32))
    myTable.reset_table()
