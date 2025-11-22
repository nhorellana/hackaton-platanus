import json
import logging
import os
import boto3
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
sqs = boto3.client("sqs")

# Get environment variables
PROBLEM_QUEUE_URL = os.environ["PROBLEM_QUEUE_URL"]

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda function to handle problem declarations, create jobs, and fan out to SQS queues.
    """
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        # 1. Input Parsing and Validation
        body = event.get('body', event)
        if isinstance(body, str):
            body = json.loads(body)

        full_declaration = body.get('full_problem_declaration')
        session_id = body.get('session_id')

        message_body = {
            'full_problem_declaration': full_declaration,
            'session_id': session_id
        }

        sqs.send_message(
            QueueUrl=PROBLEM_QUEUE_URL,
            MessageBody=json.dumps(message_body)
        )
        logger.info(f"Sent message for job {session_id} to problem queue")

        # 5. Return the Fan-Out Status
        response = {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'message': 'Orchestration complete. Jobs persisted and fanned out to SQS queues.'
            })
        }
        return response

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in request body: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Invalid JSON', 'message': str(e)})
        }
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Internal server error', 'message': str(e)})
        }
