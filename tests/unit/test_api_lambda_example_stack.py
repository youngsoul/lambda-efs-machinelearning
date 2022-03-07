import aws_cdk as core
import aws_cdk.assertions as assertions

from api_lambda_example.api_lambda_example_stack import ApiLambdaExampleStack

# example tests. To run these tests, uncomment this file along with the example
# resource in api_lambda_example/api_lambda_example_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = ApiLambdaExampleStack(app, "api-lambda-example")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
