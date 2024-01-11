"""Python Pulumi program for creating a CloudFront distribution and S3 bucket."""
import pulumi
import pulumi_aws as aws

# Import the program's configuration settings.
config = pulumi.Config()
env = config.require("env") or "dev"
owner = config.require("owner") or "owner"
web_acl = config.require("web_acl") \
    or "arn:aws:wafv2:ap-northeast-1:123456789012:global/webacl/dev-webacl"
domain = config.require("domain") or "example.com"
certificate_arn = config.require("certificate_arn") \
    or "arn:aws:acm:ap-northeast-1:123456789012:certificate/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

def setup_oai():
    """Create an Origin Access Identity (OAI) for CloudFront
    """
    oai = aws.cloudfront.OriginAccessIdentity(f"{env}-oai",
        comment="OAI for main system distribution")
    return oai

def setup_bucket(oai):
    """Create an S3 Bucket for CloudFront
    """
    bucket = aws.s3.Bucket(f"{env}-bucket",
        tags={
            "Name": f"{env}-bucket",
            "Environment": env,
            "Service": "Service Name",
            "Resource": "CloudFront_S3",
            "Owner": owner,
            "Purpose": "Purpose"},
        opts=pulumi.ResourceOptions(depends_on=[oai]))
    return bucket

def setup_bucket_policy(oai, bucket):
    """Update the S3 bucket policy to restrict access to the OAI
    """
    bucket_policy = aws.s3.BucketPolicy(f"{env}-bucket-policy",
        bucket=bucket.id,
        policy=pulumi.Output.all(bucket.arn, oai.iam_arn)
                    .apply(lambda args: f'''{{
                        "Version": "2012-10-17",
                        "Id": "PolicyForCloudFrontPrivateContent",
                        "Statement": [
                            {{
                                "Sid": "1",
                                "Effect": "Allow",
                                "Principal": {{
                                    "AWS": "{args[1]}"
                                }},
                                "Action": "s3:GetObject",
                                "Resource": "{args[0]}/*"
                            }}
                        ]
                    }}'''),
        opts=pulumi.ResourceOptions(depends_on=[bucket]))
    return bucket_policy

def setup_cloudfront_distribution(oai, bucket, policy):
    """Create a CloudFront distribution that provides HTTPS access to the S3 bucket.
    """
    ## main system distribution
    main_system_origin = f"{env}-main-system"
    flow_origin = f"{env}-flow"
    distribution = aws.cloudfront.Distribution(f"{env}-distribution",
        restrictions=aws.cloudfront.DistributionRestrictionsArgs(
            geo_restriction=aws.cloudfront.DistributionRestrictionsGeoRestrictionArgs(
                restriction_type="blacklist",
                locations=[
                    "BS",
                    "BI",
                ],
            ),
        ),
        price_class="PriceClass_200",
        enabled=True,
        is_ipv6_enabled=True,
        comment="Distribution",
        default_root_object="index.html",
        web_acl_id=web_acl,
        aliases=[domain],
        viewer_certificate=aws.cloudfront.DistributionViewerCertificateArgs(
            acm_certificate_arn=certificate_arn,
            ssl_support_method="sni-only",
            minimum_protocol_version="TLSv1.2_2021",
        ),
        origins=[
            aws.cloudfront.DistributionOriginArgs(
                domain_name=bucket.bucket_regional_domain_name,
                origin_id=main_system_origin,
                s3_origin_config=aws.cloudfront.DistributionOriginS3OriginConfigArgs(
                    origin_access_identity=oai.cloudfront_access_identity_path),
                origin_path="/main-system",
            ),
            aws.cloudfront.DistributionOriginArgs(
                domain_name=bucket.bucket_regional_domain_name,
                origin_id=flow_origin,
                s3_origin_config=aws.cloudfront.DistributionOriginS3OriginConfigArgs(
                    origin_access_identity=oai.cloudfront_access_identity_path),
            )],
        default_cache_behavior=aws.cloudfront.DistributionDefaultCacheBehaviorArgs(
            target_origin_id=main_system_origin,
            allowed_methods=[
                "GET",
                "HEAD",
            ],
            cached_methods=[
                "GET",
                "HEAD",
            ],
            forwarded_values=aws.cloudfront.DistributionDefaultCacheBehaviorForwardedValuesArgs(
                query_string=False,
                cookies=aws.cloudfront.DistributionDefaultCacheBehaviorForwardedValuesCookiesArgs(
                    forward="none",
                ),
            ),
            viewer_protocol_policy="redirect-to-https",
            min_ttl=1,
            default_ttl=300,
            max_ttl=300,
        ),
        # behaviors
        ordered_cache_behaviors=[
            aws.cloudfront.DistributionOrderedCacheBehaviorArgs(
                path_pattern="flow-images/*",
                target_origin_id=flow_origin,
                allowed_methods=[
                    "GET",
                    "HEAD",
                ],
                cached_methods=[
                    "GET",
                    "HEAD",
                ],
                forwarded_values=aws.cloudfront.DistributionOrderedCacheBehaviorForwardedValuesArgs(
                    query_string=False,
                    cookies=aws.cloudfront.DistributionOrderedCacheBehaviorForwardedValuesCookiesArgs(
                        forward="none",
                    ),
                ),
                viewer_protocol_policy="redirect-to-https",
                min_ttl=1,
                default_ttl=300,
                max_ttl=300,
            ),
        ],
        tags={
            "Environment": env,
            "Service": "Service Name",
            "Resource": "CloudFront_S3",
            "Owner": owner,
            "Purpose": "Purpose",
        },
        opts=pulumi.ResourceOptions(depends_on=[
            oai,
            policy]))
    return distribution

def add_route53_record(distribution):
    """Add a Route53 record to the distribution
    """
    hosted_zone = aws.route53.get_zone(name=f"{domain}.")

    domain_registration = aws.route53.Record(f"domain-{env}-registration",
        zone_id=hosted_zone.id,
        name=domain,
        type="A",
        aliases=[aws.route53.RecordAliasArgs(
            name=distribution.domain_name,
            zone_id=distribution.hosted_zone_id,
            evaluate_target_health=False,
        )],
        opts=pulumi.ResourceOptions(depends_on=[distribution]))
    return domain_registration

if __name__ == "__main__":
    oai, = setup_oai()
    bucket = setup_bucket(oai)
    bucket_policy = setup_bucket_policy(oai, bucket)
    try:
        cloudfront = setup_cloudfront_distribution(oai, bucket, bucket_policy)
    except:
        print("Error: CloudFront Distribution is not created.")
        raise

    domain_registration = add_route53_record(cloudfront)

    # Export the URLs of the bucket and distribution.
    pulumi.export("distribution_url",
        pulumi.Output.concat("https://", cloudfront.domain_name))
    pulumi.export("custom_domain_url",
        pulumi.Output.concat("https://", cloudfront.fqdn))
