"""This is Pulumi's AWS Python SDK sample - AWS API Gateway"""
import json
import pulumi
import pulumi_aws as aws
import pulumi_aws_apigateway as apigateway

# Load swagger file
with open('data/swagger-apigateway-sample.json', 'r', encoding='utf-8') as f:
    api = json.load(f)

# Define whole API using swagger (OpenAPI)
swagger_api = apigateway.RestAPI(
    "swagger-api",
    swagger_string=json.dumps(api),
    stage_name="dev"
)

pulumi.export("swagger-url", swagger_api.url)
