from aws_cdk import (
    Stack,
    aws_apigateway as apigw,
    aws_lambda as _lambda,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    Duration
)
from constructs import Construct

class OvoUtnBeStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Lambda para endpoint /hello
        hello_function = _lambda.Function(
            self,
            "HelloFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="hello.handler",
            code=_lambda.Code.from_asset("lib/hello"),
            description="Lambda function for hello endpoint"
        )
        
        # Crear tablas DynamoDB
        quota_table = dynamodb.Table(
            self,
            "BedrockChatbotQuota",
            table_name="BedrockChatbotQuota",
            partition_key=dynamodb.Attribute(
                name="UserID",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="Date",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST
        )
        
        progress_table = dynamodb.Table(
            self,
            "BedrockChatProgress",
            table_name="BedrockChatProgress",
            partition_key=dynamodb.Attribute(
                name="ChatID",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST
        )
        
        # Lambda para endpoint /chat (Bedrock Chatbot)
        chat_function = _lambda.Function(
            self,
            "ChatFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="chat.handler",
            code=_lambda.Code.from_asset("lib/chat"),
            timeout=Duration.minutes(5),
            description="Lambda function for chat endpoint with Bedrock integration",
            environment={
                "QUOTA_TABLE_NAME": quota_table.table_name,
                "PROGRESS_TABLE_NAME": progress_table.table_name
            }
        )
        
        # Agregar permisos DynamoDB a la Lambda
        quota_table.grant_read_write_data(chat_function)
        progress_table.grant_read_write_data(chat_function)
        
        # Agregar permisos Bedrock a la Lambda
        chat_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeModel"
                ],
                resources=["*"]
            )
        )
        
        # Crear UNA SOLA API Gateway
        api = apigw.RestApi(
            self,
            "MyApi",
            rest_api_name="OvoUtnApi",
            description="API with hello and chat endpoints"
        )
        
        # Agregar ruta /hello
        hello_resource = api.root.add_resource("hello")
        hello_resource.add_method("ANY", apigw.LambdaIntegration(hello_function))
        
        # Agregar ruta /chat
        chat_resource = api.root.add_resource("chat")
        chat_resource.add_method("ANY", apigw.LambdaIntegration(chat_function))
        
        # Crear deployment y stage
        # deployment = apigw.Deployment(
        #     self,
        #     "Deployment",
        #     api=api
        # )
        
        # stage = apigw.Stage(
        #     self,
        #     "ProdStage",
        #     deployment=deployment,
        #     stage_name="prod"
        # )
        
        # Outputs
        from aws_cdk import CfnOutput
        
        CfnOutput(
            self,
            "ApiEndpoint",
            value=f"{api.url}",
            description="API Gateway endpoint URL"
        )
        
        CfnOutput(
            self,
            "HelloEndpoint",
            value=f"{api.url}hello",
            description="Hello endpoint URL"
        )
        
        CfnOutput(
            self,
            "ChatEndpoint",
            value=f"{api.url}chat",
            description="Chat endpoint URL"
        )