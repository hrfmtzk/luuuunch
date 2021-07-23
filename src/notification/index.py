import json
import os
import typing

import boto3
import sentry_sdk
from apiclient import discovery
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.data_classes import (
    EventBridgeEvent,
    event_source,
)
from boto3.dynamodb.conditions import Key
from google.oauth2.service_account import Credentials
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

tracer = Tracer()
logger = Logger()

sentry_dsn = os.environ.get("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[AwsLambdaIntegration()],
        traces_sample_rate=1.0,
    )


def get_secret(secret_id: str) -> typing.Dict[str, typing.Any]:
    secretsmanager = boto3.client("secretsmanager")
    response = secretsmanager.get_secret_value(SecretId=secret_id)
    return json.loads(response["SecretString"])


secret = get_secret(os.environ["SECRET_ID"])


table_name = os.environ["TABLE_NAME"]
table = boto3.resource("dynamodb").Table(table_name)

icon_url = os.environ["ICON_URL"]


@logger.inject_lambda_context
@tracer.capture_lambda_handler
@event_source(data_class=EventBridgeEvent)
def lambda_handler(event: EventBridgeEvent, context) -> None:
    res = table.query(
        KeyConditionExpression=Key("PK").eq("JoinedSpace"),
    )
    spaces = [item["SK"] for item in res["Items"]]
    message = {
        "cards": [
            {
                "header": {
                    "title": "お昼だぁぁぁぁ!!!!",
                    "imageUrl": icon_url,
                },
                "sections": [
                    {
                        "widgets": [
                            {
                                "buttons": [
                                    {
                                        "textButton": {
                                            "text": "行ってきます (1 時間)",
                                            "onClick": {
                                                "action": {
                                                    "actionMethodName": "lunchStart-1h",  # noqa
                                                    "parameters": [],
                                                }
                                            },
                                        }
                                    },
                                    {
                                        "textButton": {
                                            "text": "行ってきます (30 分)",
                                            "onClick": {
                                                "action": {
                                                    "actionMethodName": "lunchStart-30m",  # noqa
                                                    "parameters": [],
                                                }
                                            },
                                        }
                                    },
                                    {
                                        "textButton": {
                                            "text": "戻りました",
                                            "onClick": {
                                                "action": {
                                                    "actionMethodName": "lunchEnd",  # noqa
                                                    "parameters": [],
                                                }
                                            },
                                        }
                                    },
                                ]
                            }
                        ],
                    },
                ],
            },
        ],
    }
    scopes = ["https://www.googleapis.com/auth/chat.bot"]
    credentials = Credentials.from_service_account_info(secret, scopes=scopes)
    chat = discovery.build("chat", "v1", credentials=credentials)

    for space in spaces:
        resp = (
            chat.spaces()
            .messages()
            .create(
                parent=space,
                body=message,
            )
            .execute()
        )
        logger.debug(resp)
