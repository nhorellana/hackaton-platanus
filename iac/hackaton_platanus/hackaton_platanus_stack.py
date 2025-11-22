from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    CfnOutput,
)
from constructs import Construct
import os

class HackatonPlatanusStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define the Lambda function
        hello_lambda = _lambda.Function(
            self, "HelloWorldFunction",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="hello_world.handler",
            code=_lambda.Code.from_asset(os.path.join(os.path.dirname(__file__), "..", "lambda")),
            timeout=Duration.seconds(30),
            memory_size=128,
            description="A simple Hello World Lambda function",
        )

        # Create API Gateway REST API
        api = apigateway.RestApi(
            self, "HelloWorldApi",
            rest_api_name="Hello World Service",
            description="API Gateway for Hello World Lambda",
            deploy_options=apigateway.StageOptions(
                stage_name="prod",
                throttling_rate_limit=100,
                throttling_burst_limit=200
            )
        )

        # Add Lambda integration to API Gateway
        hello_integration = apigateway.LambdaIntegration(
            hello_lambda,
            request_templates={"application/json": '{ "statusCode": "200" }'}
        )

        # Add GET method to the root resource
        api.root.add_method("GET", hello_integration)

        # Output the API endpoint URL
        CfnOutput(
            self, "ApiEndpoint",
            value=api.url,
            description="API Gateway endpoint URL",
            export_name="HelloWorldApiUrl"
        )

        # Output the Lambda function name
        CfnOutput(
            self, "LambdaFunctionName",
            value=hello_lambda.function_name,
            description="Lambda function name",
            export_name="HelloWorldLambdaName"
        )
