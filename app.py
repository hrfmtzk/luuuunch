#!/usr/bin/env python3
import os

from aws_cdk import core as cdk
from dotenv import find_dotenv, load_dotenv

from luuuunch.luuuunch_stack import LuuuunchStack

load_dotenv(find_dotenv())

app = cdk.App()
LuuuunchStack(
    app,
    "LuuuunchStack",
    icon_url=os.environ["ICON_URL"],
    project_id=os.environ["PROJECT_ID"],
    reply_message=os.getenv("REPLY_MESSAGE"),
    certificate_arn=os.getenv("CERTIFICATE_ARN"),
    domain_name=os.getenv("DOMAIN_NAME"),
    log_level=os.getenv("LOG_LEVEL"),
    sentry_dsn=os.getenv("SENTRY_DSN"),
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION"),
    ),
)

app.synth()
