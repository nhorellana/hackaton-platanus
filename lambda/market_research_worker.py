import json
import logging
import os
from datetime import datetime

import boto3
from shared.job_model import JobHandler

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb")
sfn_client = boto3.client("stepfunctions")

# Get environment variables
JOBS_TABLE_NAME = os.environ["JOBS_TABLE_NAME"]
STATE_MACHINE_ARN = os.environ["STATE_MACHINE_ARN"]

# Initialize job handler
job_handler = JobHandler(JOBS_TABLE_NAME)


def handler(event, context):
    """
    Market Research Worker: Starts Step Functions execution for market research.

    This Lambda is triggered by SQS messages and starts a Step Functions state machine
    that orchestrates the 5 research agents + synthesis.
    """
    logger.info(f"Market Research Worker received event: {json.dumps(event)}")

    for record in event["Records"]:
        try:
            # Parse the SQS message
            message_body = json.loads(record["body"])
            job_id = message_body["job_id"]
            session_id = message_body["session_id"]

            job = job_handler.find_one(session_id=session_id, job_id=job_id)
            if job is None:
                logger.error(f"Job {job_id} not found in session {session_id}. Skipping.")
                continue

            if job.status != 'CREATED':
                logger.warning(f"Job {job_id} in session {session_id} is not in CREATED status. Current status: {job.status}. Skipping.")
                continue

            logger.info(f"Starting Step Functions execution for job {job_id}")

            # Mark job as in progress
            job_handler.mark_in_progress(session_id=session_id, job_id=job_id)

            # Start Step Functions execution
            execution_name = f"market-research-{job_id}-{int(datetime.utcnow().timestamp())}"

            sfn_input = {
                "session_id": session_id,
                "job_id": job_id,
                "instructions": job.instructions
            }

            response = sfn_client.start_execution(
                stateMachineArn=STATE_MACHINE_ARN,
                name=execution_name,
                input=json.dumps(sfn_input)
            )

            execution_arn = response["executionArn"]

            logger.info(f"Started Step Functions execution: {execution_arn} for job {job_id}")

            # Optionally store execution ARN in DynamoDB for tracking
            try:
                dynamodb_table = dynamodb.Table(JOBS_TABLE_NAME)
                dynamodb_table.update_item(
                    Key={"session_id": session_id, "id": job_id},
                    UpdateExpression="SET execution_arn = :arn, updated_at = :updated_at",
                    ExpressionAttributeValues={
                        ":arn": execution_arn,
                        ":updated_at": datetime.utcnow().isoformat()
                    }
                )
            except Exception as update_error:
                logger.warning(f"Could not store execution ARN: {str(update_error)}")

        except Exception as e:
            logger.error(f"Error starting Step Functions execution: {str(e)}", exc_info=True)

            if "session_id" in locals() and "job_id" in locals():
                try:
                    job_handler.mark_failed(
                        session_id=session_id,
                        job_id=job_id,
                        result=str(e)
                    )
                except Exception as mark_error:
                    logger.error(f"Could not mark job as failed: {str(mark_error)}")

            # Don't raise - allow other messages in batch to process
            continue

    return {"statusCode": 200, "body": json.dumps("Successfully processed messages")}
