#!/bin/bash

# Set variables
LAMBDA_FUNCTION_NAME="ChatRAG-SendMessageHandlerDCEABF13-OZBFzP3EbBEQ"
PYTHON_FILE="index.py"
ZIP_FILE="lambda-deployment.zip"

# Step 1: Prepare your Python code
echo "Preparing Python code..."
ls *.py

# Step 2: Zip your Python code
echo "Zipping Python code..."
zip -r "$ZIP_FILE" *.py

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
