import json
import logging
import os
from boto3 import client
from botocore.exceptions import ClientError
from botocore.config import Config
from google import genai

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients
dynamodb = client('dynamodb')


def handler(event, context):
    table_name = os.environ['TABLE_NAME']

    # Initialize Gemini API client
    gemini_client = genai.Client(api_key=os.environ['GEMINI_KEY'])

    # Scan DynamoDB table
    try:
        response = dynamodb.scan(TableName=table_name)
        connections = response.get('Items', [])
    except ClientError as e:
        logger.error(f"Error scanning DynamoDB: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps('Failed to scan DynamoDB')
        }

    # Get message from the event body
    try:
        message = json.loads(event['body']).get('message')
    except (KeyError, json.JSONDecodeError) as e:
        logger.error(f"Error parsing message: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps('Invalid message format')
        }

    logger.info(f"connections: {connections}, message: {message}")

    # Get API Gateway management API endpoint
    domain_name = event['requestContext']['domainName']
    stage = event['requestContext']['stage']
    endpoint = f'https://{domain_name}/{stage}'

    callbackAPI = client('apigatewaymanagementapi', endpoint_url=endpoint)

    # Send message to the sender (Gemini integration part)
    connection_id = event['requestContext']['connectionId']

    try:
        # Send the message to Gemini API and get the response
        response = gemini_client.models.generate_content_stream(
            model="gemini-2.0-flash",
            contents=[message]
        )

        # Forward the Gemini response to the WebSocket client
        for chunk in response:
            callbackAPI.post_to_connection(
                ConnectionId=connection_id,
                Data=json.dumps({"event": "message", "data": chunk.text})
            )

        callbackAPI.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps({"event": "completed"})
        )

    except ClientError as e:
        logger.error(f"Error sending message to connection {connection_id}: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps('Failed to send messages')
        }
    except Exception as e:
        logger.error(f"Error interacting with Gemini API: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps('Error processing message with Gemini API')
        }

    return {
        'statusCode': 200,
        'body': json.dumps('Messages sent successfully')
    }
