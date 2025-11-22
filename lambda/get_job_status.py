import json
import logging
import os

import boto3
from botocore.exceptions import ClientError
from shared.job_model import JobHandler

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

# Get environment variables
JOBS_TABLE_NAME = os.environ['JOBS_TABLE_NAME']

# Get table reference
jobs_table = dynamodb.Table(JOBS_TABLE_NAME)


def handler(event, context):
    '''
    Get Job Status Lambda: Returns the current status and details of a job.

    Path: GET /jobs/{job_id}
    Returns: Job details including status, result, and metadata
    '''
    logger.info(f'Get Job Status received event: {json.dumps(event)}')

    try:
        # Extract job_id from path parameters
        job_id = event.get('pathParameters', {}).get('id')
        session_id = event.get('queryStringParameters', {}).get('session_id')

        if not job_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
                'body': json.dumps(
                    {'error': 'Missing job_id', 'message': 'job_id is required in path'}
                ),
            }

        logger.info(f'Fetching status for job {job_id}')

        job = JobHandler(JOBS_TABLE_NAME).find_one(session_id=session_id, job_id=job_id)

        # Build response
        response_data = {
            'job_id': job_id,
            'status': job.status,
            'type': job.get('type', 'unknown'),
            'instructions': job.get('instructions', ''),
            'is_final': job.status in ['COMPLETED', 'FAILED'],
            'created_at': job.get('created_at'),
            'updated_at': job.get('updated_at'),
        }

        # Add optional fields if they exist
        if 'started_at' in job:
            response_data['started_at'] = job['started_at']

        if 'completed_at' in job:
            response_data['completed_at'] = job['completed_at']

        if 'error_message' in job:
            response_data['error_message'] = job['error_message']

        # Add result for completed jobs
        if job.status == 'COMPLETED' and job.result:
            response_data['result'] = job.result

        # Add partial findings for market research jobs (for progress tracking)
        if job.get('type') == 'market_research':
            findings = {}
            if 'obstacles_findings' in job:
                findings['obstacles'] = (
                    json.loads(job['obstacles_findings'])
                    if isinstance(job['obstacles_findings'], str)
                    else job['obstacles_findings']
                )
            if 'solutions_findings' in job:
                findings['solutions'] = (
                    json.loads(job['solutions_findings'])
                    if isinstance(job['solutions_findings'], str)
                    else job['solutions_findings']
                )
            if 'legal_findings' in job:
                findings['legal'] = (
                    json.loads(job['legal_findings'])
                    if isinstance(job['legal_findings'], str)
                    else job['legal_findings']
                )
            if 'competitor_findings' in job:
                findings['competitors'] = (
                    json.loads(job['competitor_findings'])
                    if isinstance(job['competitor_findings'], str)
                    else job['competitor_findings']
                )
            if 'market_findings' in job:
                findings['market'] = (
                    json.loads(job['market_findings'])
                    if isinstance(job['market_findings'], str)
                    else job['market_findings']
                )

            if findings:
                response_data['partial_findings'] = findings

        logger.info(f'Successfully retrieved status for job {job_id}: {job.status}')

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps(response_data),
        }

    except ClientError as e:
        logger.error(f'DynamoDB error: {str(e)}', exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps(
                {'error': 'Database error', 'message': 'Failed to retrieve job status'}
            ),
        }

    except Exception as e:
        logger.error(f'Error getting job status: {str(e)}', exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps(
                {'error': 'Internal server error', 'message': str(e)}
            ),
        }
