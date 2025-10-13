from aws_cdk import (
    Stack,
    aws_apigateway as apigw,
    aws_dynamodb as dynamodb
)
from constructs import Construct

# Importar stacks modulares
from .stacks.hello_stack import HelloStack
from .stacks.chat_stack import ChatStack
from .stacks.aptitudes_stack import AptitudesStack

class OvoUtnBeStack(Stack):
    """Stack principal que orquesta todos los módulos"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Crear tablas DynamoDB centrales
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
        
        # Crear API Gateway central
        api = apigw.RestApi(
            self,
            "OvoApi",
            rest_api_name="OvoUtnApi",
            description="API para OVO"
        )
        
        # Inicializar stacks modulares
        hello_stack = HelloStack(self, "HelloStack")
        chat_stack = ChatStack(self, "ChatStack", quota_table, progress_table)
        aptitudes_stack = AptitudesStack(self, "AptitudesStack")
        
        # Agregar rutas al API Gateway
        hello_stack.add_to_api(api)
        chat_stack.add_to_api(api)
        aptitudes_stack.add_to_api(api)
        
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
        
        CfnOutput(
            self,
            "AptitudesEndpoints",
            value=f"{api.url}aptitudes/",
            description="Aptitudes endpoints: agregar, editar, eliminar, listar"
        )
