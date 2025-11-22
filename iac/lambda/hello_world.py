import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """
    Sample Lambda function that returns a greeting message.
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    # Get name from query parameters or use default
    name = event.get('queryStringParameters', {}).get('name', 'World') if event.get('queryStringParameters') else 'World'
    
    response = {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'message': f'Hello, {name}!',
            'timestamp': context.request_id,
            'function_name': context.function_name
        })
    }
    
    logger.info(f"Returning response: {json.dumps(response)}")
    return response

