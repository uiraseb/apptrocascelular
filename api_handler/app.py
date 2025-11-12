import json
import os
import uuid
import boto3
from botocore.exceptions import ClientError

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

env = {
    'DEVICES_TABLE': os.environ.get('DEVICES_TABLE', 'devices'),
    'UPLOADS_BUCKET': os.environ.get('UPLOADS_BUCKET', 'uploads-bucket'),
    'PROPOSALS_QUEUE_URL': os.environ.get('PROPOSALS_QUEUE_URL')
}

def response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(body, ensure_ascii=False)
    }

def validate_device_payload(payload):
    required = ['brand', 'model', 'condition']
    errors = []
    for f in required:
        if f not in payload:
            errors.append(f"missing: {f}")
    if payload.get('brand', '').lower() == 'redmi':
        images = payload.get('images', [])
        if len(images) < 3:
            errors.append('redmi: precisa de pelo menos 3 fotos')
    return errors

def upload_images_to_s3(images, bucket):
    urls = []
    for img in images:
        key = f"devices/{uuid.uuid4().hex}.jpg"
        try:
            s3.put_object(Bucket=bucket, Key=key, Body=b'')
            urls.append(f"s3://{bucket}/{key}")
        except ClientError:
            urls.append(f"s3://{bucket}/{key}")
    return urls

def lambda_handler(event, context):
    method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method')
    path = event.get('path', '')

    if method == 'POST' and path.endswith('/devices'):
        body = json.loads(event.get('body') or '{}')
        errors = validate_device_payload(body)
        if errors:
            return response(400, {'errors': errors})

        device_id = str(uuid.uuid4())
        images = body.get('images', [])
        image_urls = upload_images_to_s3(images, env['UPLOADS_BUCKET'])

        table = dynamodb.Table(env['DEVICES_TABLE'])
        item = {
            'id': device_id,
            'brand': body.get('brand'),
            'model': body.get('model'),
            'condition': body.get('condition'),
            'images': image_urls,
            'owner_id': body.get('owner_id'),
            'needs_manual_review': False
        }
        if item['brand'].lower() == 'redmi':
            score = 50
            if len(images) < 3:
                score -= 20
            if body.get('condition') == 'ruim':
                score -= 20
            item['score'] = max(0, score)
            if item['score'] < 40:
                item['needs_manual_review'] = True

        table.put_item(Item=item)
        return response(201, {'id': device_id, 'needs_manual_review': item['needs_manual_review']})

    if method == 'GET' and path.endswith('/devices'):
        table = dynamodb.Table(env['DEVICES_TABLE'])
        resp = table.scan(Limit=50)
        return response(200, {'items': resp.get('Items', [])})

    if method == 'POST' and path.endswith('/proposals'):
        body = json.loads(event.get('body') or '{}')
        if not body.get('from_user') or not body.get('to_user') or not body.get('device_id'):
            return response(400, {'error': 'campo obrigatório ausente'})
        sqs = boto3.client('sqs')
        queue_url = env.get('PROPOSALS_QUEUE_URL')
        if not queue_url:
            return response(500, {'error': 'queue not configured'})
        sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(body, ensure_ascii=False))
        return response(202, {'status': 'queued'})

    return response(404, {'error': 'not found'})