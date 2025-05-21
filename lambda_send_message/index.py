import json
import logging
import os
import prompt_engineering
from boto3 import client
from botocore.exceptions import ClientError
from botocore.config import Config
from google import genai

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize clients
dynamodb = client('dynamodb')

MAX_RESERVED_DIALOGS = 10

def handler(event, context):
    # retrieve name of dialogues table
    table_name = os.environ['DIALOG_TABLE_NAME']

    # Initialize Gemini API client
    gemini_client = genai.Client(api_key=os.environ['GEMINI_KEY'])

    # Get message from the event body
    try:
        question = json.loads(event['body']).get('message')
    except (KeyError, json.JSONDecodeError) as e:
        logger.error(f"Error parsing message: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps('Invalid message format')
        }

    # Get API Gateway management API endpoint
    domain_name = event['requestContext']['domainName']
    stage = event['requestContext']['stage']
    endpoint = f'https://{domain_name}/{stage}'

    callbackAPI = client('apigatewaymanagementapi', endpoint_url=endpoint)

    # Get the connection ID from the request
    connection_id = event['requestContext']['connectionId']

    logger.info(f"connection: {connection_id}, question: {question}")

    # Retrieve the chat history from DynamoDB
    try:
        history_response = dynamodb.get_item(
            TableName=table_name,
            Key={'connectionId': {'S': connection_id}}
        )
        chat_history = history_response.get('Item', {}).get('chatHistory', {}).get('L', [])

    except ClientError as e:
        logger.error(f"Error retrieving chat history for connection {connection_id}: {e}")
        chat_history = []

    # Prepare the history to send along with the new question
    if chat_history:
        chat_history_text = [item['S'] for item in chat_history]
    else:
        chat_history_text = []

    # Ensure the history does not exceed x rounds
    if len(chat_history_text) > MAX_RESERVED_DIALOGS:
        chat_history_text = chat_history_text[-MAX_RESERVED_DIALOGS:]

    # Send the chat history and new question to Gemini API
    try:
        prompt = prompt_engineering.gen_prompt_from_chat_history(chat_history_text, question)

        # Send the message to Gemini API and get the response
        response = gemini_client.models.generate_content_stream(
            model="gemini-2.0-flash",
            contents=[prompt]
        )

        # Used to store the entire answer
        answer = ""

        # Forward the Gemini response to the WebSocket client
        for chunk in response:
            answer += chunk.text
            callbackAPI.post_to_connection(
                ConnectionId=connection_id,
                Data=json.dumps({"event": "message", "data": chunk.text})
            )

        callbackAPI.post_to_connection(
            ConnectionId=connection_id,
            Data=json.dumps({"event": "completed"})
        )

        # Add the new question and answer to the conversation history
        chat_history_text.append(question)
        chat_history_text.append(answer)

        # Ensure the history does not exceed x rounds
        if len(chat_history_text) > MAX_RESERVED_DIALOGS:
            chat_history_text = chat_history_text[-MAX_RESERVED_DIALOGS:]

        # Save the chat history back to DynamoDB
        dynamodb.put_item(
            TableName=table_name,
            Item={
                'connectionId': {'S': connection_id},
                'chatHistory': {'L': [{'S': text} for text in chat_history_text]}
            }
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
