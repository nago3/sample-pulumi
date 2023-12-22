"""An AWS S3 Bucket with CloudTrail logging enabled"""
import json
import pulumi
import pulumi_aws as aws

# Create an S3 bucket for storing CloudTrail logs
s3_bucket = aws.s3.Bucket("s3-trail-bucket")

# Define the S3 Bucket Policy allowing CloudTrail to write logs
bucket_policy = aws.s3.BucketPolicy("s3-trail-bucket-policy",
    bucket=s3_bucket.id,
    policy=s3_bucket.arn.apply(lambda arn: json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AWSCloudTrailAclCheck",
                "Effect": "Allow",
                "Principal": {
                    "Service": "cloudtrail.amazonaws.com"
                },
                "Action": "s3:GetBucketAcl",
                "Resource": arn
            },
            {
                "Sid": "AWSCloudTrailWrite",
                "Effect": "Allow",
                "Principal": {
                    "Service": "cloudtrail.amazonaws.com"
                },
                "Action": "s3:PutObject",
                "Resource": f"{arn}/AWSLogs/{aws.get_caller_identity().account_id}/*",
                "Condition": {
                    "StringEquals": {
                        "s3:x-amz-acl": "bucket-owner-full-control"
                    }
                }
            }
        ]
    }))
)

# Create an AWS CloudTrail Trail
trail = aws.cloudtrail.Trail("trail",
    s3_bucket_name=s3_bucket.id,
    is_multi_region_trail=True,
    enable_log_file_validation=True,
    include_global_service_events=True
)

# Export the bucket name and trail ARN
pulumi.export('bucket_name', s3_bucket.id)
pulumi.export('trail_arn', trail.arn)
