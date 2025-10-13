from aws_cdk import (
    aws_dynamodb as dynamodb
)
from constructs import Construct

class DatabaseStack(Construct):
    """Stack centralizado para todas las tablas DynamoDB"""
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Crear tablas con nombres específicos
        # CDK creará las tablas si no existen, o las usará si ya existen
        self.quota_table = dynamodb.Table(
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
        
        self.progress_table = dynamodb.Table(
            self,
            "BedrockChatProgress",
            table_name="BedrockChatProgress",
            partition_key=dynamodb.Attribute(
                name="ChatID",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST
        )
        
        self.aptitudes_table = dynamodb.Table(
            self,
            "AptitudesTable",
            table_name="AptitudesTable",
            partition_key=dynamodb.Attribute(
                name="aptitud",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST
        )
