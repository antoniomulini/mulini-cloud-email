from __future__ import print_function
import json
import sys
import boto3

sns_topic_arn = "arn:aws:sns:eu-west-1:432173269038:GuardDuty_alerts"

def lambda_handler(event, context):
    # parsed = json.load(event)
    # print(json.dumps(event, indent=4, sort_keys=True))

    # Determine what kind of alert we have
    try:
        # is actionType key present?
        action = event['detail']['service']['action']['actionType']
    except:
        # actionType not in event JSON, quit
        print("actionType element not found in Guard Duty event")
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

    # print(message)
    # send SNS message:
    client = boto3.client('sns')
    response = client.publish(
        TopicArn = sns_topic_arn,
        Subject = 'Guard Duty Alert: '+name+' is being probed on an open port by a known malicious IP',
        Message = message
    )
    return response

if __name__ == "__main__":
    testEvent = json.loads(sys.stdin.read())
    # print(json.dumps(myEvent, indent=4))
    lambda_handler(testEvent,"NO_CONTEXT")
