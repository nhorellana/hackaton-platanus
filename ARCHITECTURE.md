# Hackaton Platanus - Architecture

## Overview

This is a distributed job processing system using AWS serverless components.

## Architecture Components

### API Gateway

- **Endpoint**: `/jobs`
- **Method**: POST
- **Payload**: `{"problem": "your problem description"}`
- **Response**: Returns a list of 3 job IDs (one for each worker type)

### Lambda Functions

#### 1. Orchestrator Lambda (`orchestrator`)

- **Trigger**: API Gateway POST /jobs
- **Function**:
  - Receives the problem description
  - Creates 3 separate jobs in DynamoDB
  - Enqueues a message to each of the 3 SQS queues
  - Returns all 3 job IDs to the caller
- **Environment Variables**:
  - `JOBS_TABLE_NAME`: DynamoDB table name
  - `SLACK_QUEUE_URL`: Slack queue URL
  - `MARKET_RESEARCH_QUEUE_URL`: Market research queue URL
  - `EXTERNAL_RESEARCH_QUEUE_URL`: External research queue URL

#### 2. Slack Worker Lambda (`slack_worker`)

- **Trigger**: Messages from `slack` SQS queue
- **Function**:
  - Processes Slack-related jobs
  - Updates job status in DynamoDB (pending → processing → completed)
  - Placeholder for Slack integration logic

#### 3. Market Research Worker Lambda (`market_research_worker`)

- **Trigger**: Messages from `market_research` SQS queue
- **Function**:
  - Processes market research jobs
  - Updates job status in DynamoDB
  - Placeholder for market analysis logic

#### 4. External Research Worker Lambda (`external_research_worker`)

- **Trigger**: Messages from `external_research` SQS queue
- **Function**:
  - Processes external research jobs
  - Updates job status in DynamoDB
  - Placeholder for external API calls and data aggregation

### SQS Queues

1. **slack** - Queue for Slack worker jobs
2. **market_research** - Queue for market research jobs
3. **external_research** - Queue for external research jobs

**Configuration**:

- Visibility timeout: 300 seconds (5 minutes)
- Message retention: 14 days
- Batch size: 1 message per Lambda invocation

### DynamoDB Table (`jobs`)

**Schema**:

- `id` (String, Partition Key) - Unique job identifier
- `status` (String) - Job status: `pending`, `processing`, `completed`, `failed`
- `instructions` (String) - The problem description
- `type` (String) - Job type: `slack`, `market_research`, `external_research`
- `result` (String) - Job result (JSON string)
- `created_at` (String) - ISO timestamp of job creation
- `updated_at` (String) - ISO timestamp of last update

**Billing Mode**: Pay per request (on-demand)

## Data Flow

1. **Client** sends POST request to `/jobs` with problem description
2. **Orchestrator Lambda**:
   - Generates 3 unique job IDs
   - Creates 3 entries in DynamoDB (one per type)
   - Sends 3 messages to respective SQS queues
   - Returns job IDs to client
3. **Worker Lambdas** (triggered by SQS):
   - Receive message from queue
   - Update job status to `processing`
   - Execute job logic
   - Update job status to `completed` with result
   - Handle errors by updating status to `failed`

## Deployment

```bash
cd /Users/cristianrodriguez/workspace/hackaton-platanus
cdk deploy
```

## Testing

### Create Jobs

```bash
curl -X POST <API_URL>/jobs \
  -H "Content-Type: application/json" \
  -d '{"problem": "analyze market trends for AI products"}'
```

**Response**:

```json
{
  "message": "Jobs created successfully",
  "jobs": [
    { "job_id": "uuid-1", "type": "slack", "status": "pending" },
    { "job_id": "uuid-2", "type": "market_research", "status": "pending" },
    { "job_id": "uuid-3", "type": "external_research", "status": "pending" }
  ],
  "job_ids": ["uuid-1", "uuid-2", "uuid-3"]
}
```

### Check Job Status (via DynamoDB)

```bash
aws dynamodb get-item \
  --table-name jobs \
  --key '{"id": {"S": "your-job-id"}}'
```

## Next Steps

### For Slack Worker:

- Implement Slack API integration
- Add webhook notifications
- Configure Slack bot token

### For Market Research Worker:

- Integrate market research APIs
- Add data analysis logic
- Implement caching for repeated queries

### For External Research Worker:

- Add external API integrations
- Implement web scraping if needed
- Add rate limiting and retry logic

### General Improvements:

- Add Dead Letter Queues (DLQ) for failed messages
- Implement CloudWatch alarms for monitoring
- Add API authentication (API keys, Cognito, etc.)
- Add pagination for job status queries
- Implement webhooks for job completion notifications
- Add S3 storage for large results
