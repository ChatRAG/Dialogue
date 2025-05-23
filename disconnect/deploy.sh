#!/bin/bash

# Set variables
LAMBDA_FUNCTION_NAME="ChatRAG-DisconnectHandlerCB7ED6F7-5X3uUdnLM11M"
PYTHON_FILE="index.py"
ZIP_FILE="lambda-deployment.zip"

# Step 1: Prepare your Python code
echo "Preparing Python code..."
if [ ! -f "$PYTHON_FILE" ]; then
  echo "Error: $PYTHON_FILE does not exist. Please ensure your Lambda function code is ready."
  exit 1
fi

# Step 2: Zip your Python code
echo "Zipping Python code..."
zip -r "$ZIP_FILE" "$PYTHON_FILE"

# Step 3: Deploy to AWS Lambda using AWS CLI
echo "Deploying to AWS Lambda..."
aws lambda update-function-code \
  --function-name "$LAMBDA_FUNCTION_NAME" \
  --zip-file fileb://"$ZIP_FILE"

# Check if the deployment was successful
if [ $? -eq 0 ]; then
  echo "Deployment successful!"
else
  echo "Deployment failed. Please check the error messages above."
fi

rm "$ZIP_FILE"
