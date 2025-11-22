import json
import logging
import os
import uuid
from datetime import datetime
from decimal import Decimal

from shared.anthropic import Anthropic, ConversationMessage

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

# Get environment variables
CHAT_SESSIONS_TABLE_NAME = os.environ['CHAT_SESSIONS_TABLE_NAME']
ANTHROPIC_API_KEY = os.environ['ANTHROPIC_API_KEY']

# Get table reference
chat_sessions_table = dynamodb.Table(CHAT_SESSIONS_TABLE_NAME)


class DecimalEncoder(json.JSONEncoder):
    '''Helper class to convert DynamoDB Decimal types to JSON'''

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def handler(event, context):
    '''
    Chat conversation manager Lambda function.
    Manages chat sessions and interfaces with AI API (e.g., Claude).

    Expected payload:
    {
        'message': 'user message here',
        'session_id': 'optional-session-id'
    }
    '''
    logger.info(f'Received event: {json.dumps(event)}')

    try:
        # Parse the request body
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event

        # Extract parameters
        message = body.get('message')
        session_id = body.get('session_id')

        # Validate required parameters
        if not message:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps(
                    {
                        'error': 'Missing required parameter: message',
                        'message': 'Please provide a "message" field',
                    }
                ),
            }

        # Generate session_id if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.info(f'Generated new session_id: {session_id}')

        logger.info(f'Processing message for session {session_id}: {message}')

        # Get conversation history
        conversation_history = get_conversation_history(session_id)

        # Add user message to history
        user_message = ConversationMessage(
            role='user',
            content=message,
            timestamp=datetime.utcnow().isoformat(),
        )
        conversation_history.append(user_message)

        # Call AI API (placeholder - implement your actual AI integration)
        anthropic = Anthropic(ANTHROPIC_API_KEY)
        ai_response = anthropic.send_message(conversation_history, message)

        # Add AI response to history
        assistant_message = ConversationMessage(
            role='assistant',
            content=ai_response,
            timestamp=datetime.utcnow().isoformat(),
        )
        conversation_history.append(assistant_message)

        # Store both messages in DynamoDB
        store_message(session_id, user_message)
        store_message(session_id, assistant_message)

        # Prepare response
        response = {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps(
                {
                    'session_id': session_id,
                    'message': ai_response,
                    'conversation_length': len(conversation_history),
                    'timestamp': datetime.utcnow().isoformat(),
                }
            ),
        }

        logger.info(f'Successfully processed message for session {session_id}')
        return response

    except json.JSONDecodeError as e:
        logger.error(f'Invalid JSON in request body: {str(e)}')
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Invalid JSON', 'message': str(e)}),
        }
    except Exception as e:
        logger.error(f'Error processing chat: {str(e)}', exc_info=True)
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Internal server error', 'message': str(e)}),
        }


def get_conversation_history(session_id, limit=50):
    '''
    Retrieve conversation history for a session from DynamoDB.

    Args:
        session_id: The session identifier
        limit: Maximum number of messages to retrieve (default: 50)

    Returns:
        List of messages in chronological order
    '''
    try:
        response = chat_sessions_table.query(
            KeyConditionExpression=(boto3.dynamodb.conditions.Key('session_id').eq(session_id)),
            Limit=limit,
            ScanIndexForward=True,  # Sort by timestamp ascending
        )

        messages = []
        for item in response.get('Items', []):
            messages.append(
                {
                    'role': item.get('role'),
                    'content': item.get('content'),
                    'timestamp': item.get('timestamp'),
                }
            )

        logger.info(f'Retrieved {len(messages)} messages for session {session_id}')
        return messages

    except Exception as e:
        logger.error(f'Error retrieving conversation history: {str(e)}', exc_info=True)
        return []


def store_message(session_id, message):
    '''
    Store a message in DynamoDB.

    Args:
        session_id: The session identifier
        message: Message dict with role, content, and timestamp
    '''
    try:
        item = {
            'session_id': session_id,
            'timestamp': message['timestamp'],
            'role': message['role'],
            'content': message['content'],
            'created_at': datetime.utcnow().isoformat(),
        }

        chat_sessions_table.put_item(Item=item)
        logger.info(f"Stored {message['role']} message for session {session_id}")

    except Exception as e:
        logger.error(f'Error storing message: {str(e)}', exc_info=True)
        raise
