import boto3
import json
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize the Lambda client
lambda_client = boto3.client('lambda')


def recall_chunks(query):
    payload = json.dumps(
        {
            'query': query,
        }
    )

    # Invoke the Lambda function
    response = lambda_client.invoke(
        FunctionName="ChatRAG-Search-QueryChunk",
        InvocationType='RequestResponse',  # Use 'Event' for async invocation
        Payload=payload
    )

    # Read the response
    response_payload = response['Payload'].read().decode('utf-8')
    response = json.loads(response_payload)

    if response['statusCode'] == 200:
        response_body = json.loads(response['body'])
        results = response_body['results']

        key2chunks = {}
        for result in results:
            if result['file_key'] not in key2chunks:
                key2chunks[result['file_key']] = []
            key2chunks[result['file_key']].append(result)

        for key, _ in key2chunks.items():
            key2chunks[key].sort(key=lambda x: x['offset'])

        return key2chunks

    return {}
