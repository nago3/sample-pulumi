"""This is Pulumi's AWS Python SDK sample - AWS API Gateway Lambda"""
import pulumi
import pulumi_aws as aws

# Get the current stack reference
config = pulumi.Config()
env = config.require("env") or "dev"
owner = config.require("owner") or "owner"
lambda_function_name = config.require("lambda_function_name") or f"{env}-lambda-function"

def setup_api_gateway_lambda():
    """Setup API Gateway and Lambda
    """
    # Create an API Gateway Rest API
    api = aws.apigateway.RestApi("api",
        description="Resource description",
        tags={
            "Name": f"{env}-resource",
            "Environment": env,
            "Service": "Service Name",
            "Resource": "API Gateway",
            "Owner": owner,
            "Purpose": "Purpose"})
    # Reference to existing lambda function
    lambda_function = aws.lambda_.Function.get("lambda_function", lambda_function_name)
    lambda_function_arn = lambda_function.invoke_arn
    # invoke the function from API GateCreate a Lambda permission to way
    invoke_permission = aws.lambda_.Permission("invoke-permission",
        action="lambda:InvokeFunction",
        function=lambda_function_name,
        principal="apigateway.amazonaws.com",
        source_arn=api.execution_arn.apply(lambda arn: arn + "/*/*"))
    return api, lambda_function_arn

def setup_api_gateway_resources_methods(api, lambda_arn):
    """Setup API Gateway resources and methods

    API design:
        /v1 - ROOT
            /flow
                /item-suggestions
    """
    # /v1
    resource_v1 = aws.apigateway.Resource("resource-v1",
        rest_api=api.id,
        parent_id=api.root_resource_id,
        path_part="v1")
    ## /v1/item-suggestions
    resource_item_suggestions = aws.apigateway.Resource("resource-item-suggestions",
        rest_api=api.id,
        parent_id=resource_v1.id,
        path_part="item-suggestions",
        opts=pulumi.ResourceOptions(depends_on=[resource_v1]))
    ## /v1/item-suggestions OPTIONS
    resource_item_suggestions_option_method = aws.apigateway.Method("resource-item-suggestions-option-method",
        rest_api=api.id,
        resource_id=resource_item_suggestions.id,
        http_method="OPTIONS",
        authorization="NONE",
        opts=pulumi.ResourceOptions(depends_on=[resource_item_suggestions]))
    resource_item_suggestions_option_integration = aws.apigateway.Integration("resource-item-suggestions-option-integration",
        rest_api=api.id,
        resource_id=resource_item_suggestions.id,
        http_method=resource_item_suggestions_option_method.http_method,
        integration_http_method="OPTIONS",
        type="MOCK",
        uri=lambda_function_arn,
        request_templates={
            "application/json": "{\"statusCode\": 200}"
        },
        opts=pulumi.ResourceOptions(depends_on=[
                                        resource_item_suggestions,
                                        resource_item_suggestions_option_method]))
    ## /v1/item-suggestions POST
    resource_item_suggestions_post_method = aws.apigateway.Method("resource-item-suggestions-post-method",
        rest_api=api.id,
        resource_id=resource_item_suggestions.id,
        http_method="POST",
        authorization="NONE",
        opts=pulumi.ResourceOptions(depends_on=[resource_item_suggestions]))
    resource_item_suggestions_post_integration = aws.apigateway.Integration("resource-item-suggestions-post-integration",
        rest_api=api.id,
        resource_id=resource_item_suggestions.id,
        http_method=resource_item_suggestions_post_method.http_method,
        integration_http_method="POST",
        type="AWS_PROXY",
        uri=lambda_function_arn,
        opts=pulumi.ResourceOptions(depends_on=[
                                        resource_item_suggestions,
                                        resource_item_suggestions_post_method]))
    return resource_item_suggestions_option_integration, resource_item_suggestions_post_integration

def deploy_api_gateway(api, post_integration, option_integration):
    """Deploy API Gateway
    """
    deployment = aws.apigateway.Deployment("deployment",
        rest_api=api.id,
        stage_name="prod",
        opts=pulumi.ResourceOptions(depends_on=[
                                        post_integration,
                                        option_integration]))
    return deployment


if __name__ == "__main__":
    api, lambda_function_arn = setup_api_gateway_lambda()
    post_integration, option_integration = setup_api_gateway_resources_methods(api, lambda_function_arn)
    try:
        deployment = deploy_api_gateway(api, post_integration, option_integration)
    except:
        print("Error: API Gateway is not created.")
        raise

    pulumi.export("api_gateway_url",
        pulumi.Output.concat(deployment.invoke_url))
