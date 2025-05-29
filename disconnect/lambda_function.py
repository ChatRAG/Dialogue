import os
import boto3
from botocore.exceptions import ClientError

def handler(event, context):
    # Initialize DynamoDB client and document client
    conn_client = boto3.resource('dynamodb').Table(os.environ['CONNECTION_TABLE_NAME'])
    dialog_client = boto3.resource('dynamodb').Table(os.environ['DIALOG_TABLE_NAME'])

    # Prepare the key to delete from DynamoDB
    conn_key = {
        'connectionId': event['requestContext']['connectionId']
    }
    dialog_key = {
        'connectionId': event['requestContext']['connectionId']
    }

    # Try deleting the item from DynamoDB
    try:
        conn_client.delete_item(Key=conn_key)
        dialog_client.delete_item(Key=dialog_key)
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
