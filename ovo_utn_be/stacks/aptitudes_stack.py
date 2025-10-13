from aws_cdk import (
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_dynamodb as dynamodb
)
from constructs import Construct

class AptitudesStack(Construct):
    """Stack para funcionalidad de Aptitudes"""
    
    def __init__(self, scope: Construct, construct_id: str, database_stack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Usar tabla del database_stack
        self.aptitudes_table = database_stack.aptitudes_table
        
        # Lambda unificada para gestión de aptitudes
        self.aptitudes_function = _lambda.Function(
            self,
            "AptitudesFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="aptitudes_unified.handler",
            code=_lambda.Code.from_asset("lib/aptitudes"),
            description="Lambda function for managing aptitudes (unified)",
            environment={
                "APTITUDES_TABLE_NAME": self.aptitudes_table.table_name
            }
        )
        
        # Agregar permisos DynamoDB
        self.aptitudes_table.grant_read_write_data(self.aptitudes_function)
    
    def add_to_api(self, api: apigw.RestApi):
        """Agregar rutas al API Gateway"""
        aptitudes_resource = api.root.add_resource("aptitudes")
        
        # POST /aptitudes/agregar
        agregar_resource = aptitudes_resource.add_resource("agregar")
        agregar_resource.add_method("POST", apigw.LambdaIntegration(self.aptitudes_function))
        
        # PUT /aptitudes/editar
        editar_resource = aptitudes_resource.add_resource("editar")
        editar_resource.add_method("PUT", apigw.LambdaIntegration(self.aptitudes_function))
        
        # DELETE /aptitudes/eliminar
        eliminar_resource = aptitudes_resource.add_resource("eliminar")
        eliminar_resource.add_method("DELETE", apigw.LambdaIntegration(self.aptitudes_function))
        
        # GET /aptitudes/listar
        listar_resource = aptitudes_resource.add_resource("listar")
        listar_resource.add_method("GET", apigw.LambdaIntegration(self.aptitudes_function))
