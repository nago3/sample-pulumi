"""AWS SNS Topic and EventBridge Rule for Spot Instance Interruption"""
import pulumi
import pulumi_aws as aws

# Get the current stack reference
config = pulumi.Config()
env  = config.require("env") or "dev"
email = config.require("email") or "mail@exmaple.com"
owner = config.require("owner") or "owner"

# Create a new SNS topic to send notifications to
topic = aws.sns.Topic("NotifSpotInstanceInterruption",
    name="NotifSpotInstanceInterruption",
    display_name="NotifSpotInstanceInterruption",
    tags={
        "Name": "NotifSpotInstanceInterruption",
        "Environment": env,
        "Service": "Service Name",
        "Resource": "SNS",
        "Owner": owner,
        "Purpose": "EventBridge Scheduler"})

email_subscription = aws.sns.TopicSubscription("emailSubscription",
    topic=topic.arn,
    protocol="email",
    endpoint=email)

# Create a new EventBus
event_bus = aws.cloudwatch.EventBus("eventbus",
    name="eventbus-scheduler")

# Create a new EventBridge rule for spotting instance interruptions
event_rule = aws.cloudwatch.EventRule("NotifSpotInstanceInterruptionEvent",
    name="NotifSpotInstanceInterruptionEvent",
    event_bus_name=event_bus.name,
    event_pattern="""
    {
        "source": ["aws.ec2"],
        "detail-type": ["EC2 Spot Instance Interruption Warning"]
    }
    """)

# Set the SNS topic as the target for the EventBridge rule
rule_target = aws.cloudwatch.EventTarget("SendToSNS",
    rule=event_rule.name,
    arn=topic.arn,
    event_bus_name=event_bus.name)

pulumi.export('sns_topic_arn', topic.arn)
pulumi.export('event_rule_name', event_rule.name)
pulumi.export('event_bus_name', event_bus.name)
