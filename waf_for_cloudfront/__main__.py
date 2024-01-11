"""Python Pulumi program for creating a Web_acl for CloudFront"""
import pulumi
import pulumi_aws as aws

# Import the program's configuration settings.
config = pulumi.Config()
env = config.require("env") or "dev"
owner = config.require("owner") or "owner"

def setup_webacl():
    """Create a WAFv2 Web ACL for a CloudFront distribution
    """
    acl = aws.wafv2.WebAcl(f"{env}-webacl",
        scope="CLOUDFRONT",
        description=f"{env} webacl",
        default_action=aws.wafv2.WebAclDefaultActionArgs(
            allow=aws.wafv2.WebAclDefaultActionAllowArgs()),
        visibility_config=aws.wafv2.WebAclVisibilityConfigArgs(
            cloudwatch_metrics_enabled=False,
            metric_name=f"{env}-webacl",
            sampled_requests_enabled=True))
    return acl


if __name__ == "__main__":
    web_acl = setup_webacl()

    # Export waf webacl ARN
    pulumi.export("web_acl_arn", web_acl.arn)
