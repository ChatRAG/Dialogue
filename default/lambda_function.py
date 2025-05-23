import json
import boto3
from botocore.exceptions import ClientError


def handler(event, context):
    connection_id = event['requestContext']['connectionId']

    # Create a client for API Gateway Management API
    client = boto3.client('apigatewaymanagementapi',
                          endpoint_url=f"https://{event['requestContext']['domainName']}/{event['requestContext']['stage']}")

    try:
        # Get connection info
        response = client.get_connection(ConnectionId=connection_id)
    except ClientError as e:
        print(f"Error getting connection info: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Failed to retrieve connection information.'})
        }

    # Add the connection ID to the response
    connection_info = response
    connection_info['connectionID'] = connection_id

    # Send a message to the connection
    try:
        client.post_to_connection(
            ConnectionId=connection_id,
            Data=f"Use the sendmessage route to send a message. Your info: {json.dumps(connection_info)}"
        )
    except ClientError as e:
        print(f"Error posting to connection: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Failed to send message to connection.'})
        }

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Message sent successfully'})
    }
