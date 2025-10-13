from aws_cdk import (
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    Duration
)
from constructs import Construct

class ChatStack(Construct):
    """Stack para funcionalidad Chat con Bedrock"""
    
    def __init__(self, scope: Construct, construct_id: str, quota_table, progress_table, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Usar tablas pasadas como parámetros
        self.quota_table = quota_table
        self.progress_table = progress_table
        
        # Lambda para endpoint /chat
        self.chat_function = _lambda.Function(
            self,
            "ChatFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="chat.handler",
            code=_lambda.Code.from_asset("lib/chat"),
            timeout=Duration.minutes(5),
            description="Lambda function for chat endpoint with Bedrock integration",
            environment={
                "QUOTA_TABLE_NAME": self.quota_table.table_name,
                "PROGRESS_TABLE_NAME": self.progress_table.table_name
            }
        )
        
        # Agregar permisos
        self.quota_table.grant_read_write_data(self.chat_function)
        self.progress_table.grant_read_write_data(self.chat_function)
        
        self.chat_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["bedrock:InvokeModel"],
                resources=["*"]
            )
        )
    
    def add_to_api(self, api: apigw.RestApi):
        """Agregar rutas al API Gateway"""
        chat_resource = api.root.add_resource("chat")
        chat_resource.add_method("ANY", apigw.LambdaIntegration(self.chat_function))
