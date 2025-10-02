import aws_cdk as core
import aws_cdk.assertions as assertions

from ovo_utn_be.ovo_utn_be_stack import OvoUtnBeStack

# example tests. To run these tests, uncomment this file along with the example
# resource in ovo_utn_be/ovo_utn_be_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = OvoUtnBeStack(app, "ovo-utn-be")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
