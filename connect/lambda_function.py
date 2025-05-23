import os
import boto3
from botocore.exceptions import ClientError

def handler(event, context):
    # Initialize DynamoDB client and document client
    dynamodb_client = boto3.client('dynamodb')
    doc_client = boto3.resource('dynamodb').Table(os.environ['TABLE_NAME'])

    # Prepare the item to be inserted into DynamoDB
    item = {
        'connectionId': event['requestContext']['connectionId']
    }

    # Try inserting the item into DynamoDB
    try:
        doc_client.put_item(Item=item)
    except ClientError as err:
        print(f"Error putting item into DynamoDB: {err}")
        return {
            'statusCode': 500,
            'body': 'Failed to insert item into DynamoDB.'
        }

    return {
        'statusCode': 200,
        'body': 'Item successfully inserted into DynamoDB.'
    }