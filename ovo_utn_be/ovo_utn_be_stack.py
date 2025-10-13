from aws_cdk import (
    Stack,
    aws_apigateway as apigw
)
from constructs import Construct

# Importar stacks modulares
from .stacks.database_stack import DatabaseStack
from .stacks.hello_stack import HelloStack
from .stacks.chat_stack import ChatStack
from .stacks.aptitudes_stack import AptitudesStack

class OvoUtnBeStack(Stack):
    """Stack principal que orquesta todos los módulos"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Crear stack de base de datos centralizado
        database_stack = DatabaseStack(self, "DatabaseStack")
        
        # Crear API Gateway central
        api = apigw.RestApi(
            self,
            "OvoApi",
            rest_api_name="OvoUtnApi",
            description="API para OVO"
        )
        
        # Inicializar stacks modulares (sin pasar tablas)
        hello_stack = HelloStack(self, "HelloStack")
        chat_stack = ChatStack(self, "ChatStack", database_stack)
        aptitudes_stack = AptitudesStack(self, "AptitudesStack", database_stack)
        
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
