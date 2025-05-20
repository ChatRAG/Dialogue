import os
import boto3
from botocore.exceptions import ClientError

def handler(event, context):
    # Initialize DynamoDB client and document client
    dynamodb_client = boto3.client('dynamodb')
    doc_client = boto3.resource('dynamodb').Table(os.environ['TABLE_NAME'])

    # Prepare the key to delete from DynamoDB
    key = {
        'connectionId': event['requestContext']['connectionId']
    }

    # Try deleting the item from DynamoDB
    try:
        doc_client.delete_item(Key=key)
    except ClientError as err:
        print(f"Error deleting item from DynamoDB: {err}")
        return {
            'statusCode': 500,
            'body': 'Failed to delete item from DynamoDB.'
        }

    return {
        'statusCode': 200,
        'body': 'Item successfully deleted from DynamoDB.'
    }
