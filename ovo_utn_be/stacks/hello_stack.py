from aws_cdk import (
    aws_lambda as _lambda,
    aws_apigateway as apigw
)
from constructs import Construct

class HelloStack(Construct):
    """Stack para funcionalidad Hello"""
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Lambda para endpoint /hello
        self.hello_function = _lambda.Function(
            self,
            "HelloFunction",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="hello.handler",
            code=_lambda.Code.from_asset("lib/hello"),
            description="Lambda function for hello endpoint"
        )
    
    def add_to_api(self, api: apigw.RestApi):
        """Agregar rutas al API Gateway"""
        hello_resource = api.root.add_resource("hello")
        hello_resource.add_method("ANY", apigw.LambdaIntegration(self.hello_function))
