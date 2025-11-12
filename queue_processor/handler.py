import json
import os
import boto3
from botocore.exceptions import ClientError

sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

env = {
    'DEVICES_TABLE': os.environ.get('DEVICES_TABLE', 'devices'),
    'NOTIFICATIONS_TOPIC_ARN': os.environ.get('NOTIFICATIONS_TOPIC_ARN')
}

def lambda_handler(event, context):
    for record in event.get('Records', []):
        body = json.loads(record['body'])
        process_proposal(body)
    return {'status': 'ok'}

def process_proposal(proposal):
    table = dynamodb.Table(env['DEVICES_TABLE'])
    device_id = proposal.get('device_id')
    try:
        resp = table.get_item(Key={'id': device_id})
    except ClientError:
        return
    item = resp.get('Item')
    if not item:
        return
    if item.get('status') == 'available' or 'status' not in item:
        proposals = item.get('proposals', [])
        proposals.append({
            'from_user': proposal.get('from_user'),
            'to_user': proposal.get('to_user'),
            'comment': proposal.get('comment'),
            'id': proposal.get('id') or proposal.get('device_id') + '-' + proposal.get('from_user')
        })
        table.update_item(
            Key={'id': device_id},
            UpdateExpression='SET proposals = :p',
            ExpressionAttributeValues={':p': proposals}
        )
        topic = env.get('NOTIFICATIONS_TOPIC_ARN')
        if topic:
            sns.publish(TopicArn=topic, Message=json.dumps({'device_id': device_id, 'type': 'proposal'}), Subject='Nova proposta')
