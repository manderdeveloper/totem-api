import json
import boto3
import os

WEBSOCKET_URL=os.environ.get('WEBSOCKET_URL')
DYNAMO_TABLE=os.environ.get('DYNAMO_TABLE')

apigatewaymanagementapi = boto3.client('apigatewaymanagementapi', endpoint_url=WEBSOCKET_URL)
dynamodb = boto3.client('dynamodb')

def lambda_handler(event, context):
    requestContext = event.get('requestContext', {})
    routeKey = requestContext.get('routeKey')
    connection_id = requestContext.get('connectionId')
    
    if routeKey == '$connect':
        item = { 'connectionId': {'S': connection_id} }
        dynamodb.put_item( TableName=DYNAMO_TABLE, Item=item )
        return { 'statusCode': 200 }
    
    elif routeKey == '$disconnect':
        dynamodb.delete_item( TableName=DYNAMO_TABLE, Key={ 'connectionId': {'S': connection_id} })
        return { 'statusCode': 200 }
        
    body = event.get('body', '{}')
    message = json.loads(body)
    if message and message['action'] == 'launchGame':
        send_message_to_all_clients(message)
    if message and message['action'] == 'totem_touched':
        send_message_to_all_clients({'action': 'winner', 'data': {'winner': connection_id}})
        
    return { 'statusCode': 200 }


def send_message_to_client(connection_id, message):
    apigatewaymanagementapi.post_to_connection(
        ConnectionId=connection_id,
        Data=json.dumps(message)
    )

def send_message_to_all_clients(message):
    connected_clients = get_conected_clients()
    for connection_id in connected_clients:
        send_message_to_client(connection_id, message)

def get_conected_clients():
    response = dynamodb.scan(TableName=DYNAMO_TABLE)
    connected_clients = [item['connectionId']['S'] for item in response['Items']]
    return connected_clients
