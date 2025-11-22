from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_sqs as sqs,
    aws_dynamodb as dynamodb,
    aws_lambda_event_sources as lambda_event_sources,
    CfnOutput,
    RemovalPolicy,
)
from constructs import Construct
import os


class HackatonPlatanusStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        lambda_code_path = os.path.join(
            os.path.dirname(__file__), "..", "lambda"
        )

        # Create DynamoDB table for jobs
        jobs_table = dynamodb.Table(
            self, "JobsTable",
            table_name="jobs",
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            point_in_time_recovery=True
        )

        # Create SQS Queues
        slack_queue = sqs.Queue(
            self, "SlackQueue",
            queue_name="slack",
            visibility_timeout=Duration.seconds(300),
            retention_period=Duration.days(14)
        )

        market_research_queue = sqs.Queue(
            self, "MarketResearchQueue",
            queue_name="market_research",
            visibility_timeout=Duration.seconds(300),
            retention_period=Duration.days(14)
        )

        external_research_queue = sqs.Queue(
            self, "ExternalResearchQueue",
            queue_name="external_research",
            visibility_timeout=Duration.seconds(300),
            retention_period=Duration.days(14)
        )

        # Define the Orchestrator Lambda function
        orchestrator_lambda = _lambda.Function(
            self, "OrchestratorFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="orchestrator.handler",
            code=_lambda.Code.from_asset(lambda_code_path),
            timeout=Duration.seconds(30),
            memory_size=256,
            description="Orchestrator Lambda that processes job requests",
            function_name="orchestrator",
            environment={
                "JOBS_TABLE_NAME": jobs_table.table_name,
                "SLACK_QUEUE_URL": slack_queue.queue_url,
                "MARKET_RESEARCH_QUEUE_URL": market_research_queue.queue_url,
                "EXTERNAL_RESEARCH_QUEUE_URL": (
                    external_research_queue.queue_url
                ),
                "ANTHROPIC_API_KEY": "Llenar con la key"  # Replace with actual key or use Secrets Manager
            }
        )

        # Grant permissions to orchestrator
        jobs_table.grant_write_data(orchestrator_lambda)
        slack_queue.grant_send_messages(orchestrator_lambda)
        market_research_queue.grant_send_messages(orchestrator_lambda)
        external_research_queue.grant_send_messages(orchestrator_lambda)

        # Create worker Lambda functions
        slack_worker = _lambda.Function(
            self, "SlackWorker",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="slack_worker.handler",
            code=_lambda.Code.from_asset(lambda_code_path),
            timeout=Duration.seconds(300),
            memory_size=512,
            description="Processes Slack jobs",
            function_name="slack_worker",
            environment={
                "JOBS_TABLE_NAME": jobs_table.table_name
            }
        )

        market_research_worker = _lambda.Function(
            self, "MarketResearchWorker",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="market_research_worker.handler",
            code=_lambda.Code.from_asset(lambda_code_path),
            timeout=Duration.seconds(300),
            memory_size=512,
            description="Processes market research jobs",
            function_name="market_research_worker",
            environment={
                "JOBS_TABLE_NAME": jobs_table.table_name
            }
        )

        external_research_worker = _lambda.Function(
            self, "ExternalResearchWorker",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="external_research_worker.handler",
            code=_lambda.Code.from_asset(lambda_code_path),
            timeout=Duration.seconds(300),
            memory_size=512,
            description="Processes external research jobs",
            function_name="external_research_worker",
            environment={
                "JOBS_TABLE_NAME": jobs_table.table_name
            }
        )

        # Grant DynamoDB permissions to workers
        jobs_table.grant_read_write_data(slack_worker)
        jobs_table.grant_read_write_data(market_research_worker)
        jobs_table.grant_read_write_data(external_research_worker)

        # Connect queues to worker lambdas
        slack_worker.add_event_source(
            lambda_event_sources.SqsEventSource(
                slack_queue,
                batch_size=1
            )
        )

        market_research_worker.add_event_source(
            lambda_event_sources.SqsEventSource(
                market_research_queue,
                batch_size=1
            )
        )

        external_research_worker.add_event_source(
            lambda_event_sources.SqsEventSource(
                external_research_queue,
                batch_size=1
            )
        )

        # Create API Gateway REST API
        api = apigateway.RestApi(
            self, "JobsApi",
            rest_api_name="Jobs Service",
            description="API Gateway for job orchestration",
            deploy_options=apigateway.StageOptions(
                stage_name="prod",
                throttling_rate_limit=100,
                throttling_burst_limit=200
            )
        )

        # Create /jobs resource
        jobs_resource = api.root.add_resource("jobs")

        # Add Lambda integration to API Gateway
        orchestrator_integration = apigateway.LambdaIntegration(
            orchestrator_lambda,
            proxy=True
        )

        # Add POST method to /jobs endpoint
        jobs_resource.add_method("POST", orchestrator_integration)

        # Add CORS support
        jobs_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_methods=["POST", "OPTIONS"],
            allow_headers=["Content-Type", "Authorization"]
        )

        # Output the API endpoint URL
        CfnOutput(
            self, "ApiEndpoint",
            value=api.url,
            description="API Gateway endpoint URL",
            export_name="JobsApiUrl"
        )

        # Output the /jobs endpoint URL
        CfnOutput(
            self, "JobsEndpoint",
            value=f"{api.url}jobs",
            description="Jobs endpoint URL",
            export_name="JobsEndpointUrl"
        )

        # Output the Lambda function names
        CfnOutput(
            self, "OrchestratorFunctionName",
            value=orchestrator_lambda.function_name,
            description="Orchestrator Lambda function name",
            export_name="OrchestratorLambdaName"
        )

        # Output queue URLs
        CfnOutput(
            self, "SlackQueueUrl",
            value=slack_queue.queue_url,
            description="Slack queue URL"
        )

        CfnOutput(
            self, "MarketResearchQueueUrl",
            value=market_research_queue.queue_url,
            description="Market research queue URL"
        )

        CfnOutput(
            self, "ExternalResearchQueueUrl",
            value=external_research_queue.queue_url,
            description="External research queue URL"
        )

        # Output DynamoDB table name
        CfnOutput(
            self, "JobsTableName",
            value=jobs_table.table_name,
            description="Jobs DynamoDB table name"
        )
