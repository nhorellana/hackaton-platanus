import json
import logging
import os
from shared.job_model import JobHandler

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get environment variables
JOBS_TABLE_NAME = os.environ["JOBS_TABLE_NAME"]

# Get table reference
job_handler = JobHandler(JOBS_TABLE_NAME)


def handler(event, context):
    """
    External Research worker Lambda that processes messages from the queue.
    """
    logger.info(f"Received event: {json.dumps(event)}")

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

            job_handler.mark_in_progress(session_id=session_id, job_id=job_id)

            logger.info(f"Processing External Research job {job_id}")

            # TODO: Add your external research logic here
            # For now, we'll simulate some work
            result = process_external_research_job(instructions=job.instructions)

            job_handler.mark_completed(
                session_id=session_id,
                job_id=job_id,
                result=result,
            )

            logger.info(f"Completed External Research job {job_id}")

        except Exception as e:
            logger.error(
                f"Agent execution failed for job {job_id}: {str(e)}", exc_info=True
            )

            job_handler.mark_failed(
                session_id=session_id,
                job_id=job_id,
                result=str(e)
            )

            raise
    
    return {"statusCode": 200, "body": json.dumps("Successfully processed messages")}


def process_external_research_job(instructions):
    """
    Process the external research job based on instructions.
    This is a placeholder - implement your actual logic here.
    """
    logger.info(f"Processing external research instructions: {instructions}")

    # TODO: Implement actual external research logic
    # For example:
    # - Call external APIs
    # - Scrape websites for data
    # - Query external databases
    # - Aggregate data from multiple sources

    result = {
        "message": "External research job processed successfully",
        "instructions": instructions,
        "data_sources": ["External API 1", "External API 2", "Public Database"],
        "findings": {
            "key_insights": [
                "Insight 1 from external research",
                "Insight 2 from external research",
                "Insight 3 from external research",
            ],
            "data_points": {
                "metric_1": "42%",
                "metric_2": "1.5M users",
                "metric_3": "$250K average",
            },
        },
        "references": [
            "https://example.com/source1",
            "https://example.com/source2",
            "https://example.com/source3",
        ],
    }

    return json.dumps(result)
