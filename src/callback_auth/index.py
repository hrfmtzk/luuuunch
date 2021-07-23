import os
import typing

import sentry_sdk
from aws_lambda_powertools import Logger, Tracer
from oauth2client import client
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


class UnverifiedError(Exception):
    def __init__(self, message: str, *args: object) -> None:
        super().__init__(*args)
        self.message = message


def verify_token(id_token: str) -> bool:
    CHAT_ISSUER = "chat@system.gserviceaccount.com"
    PUBLIC_CERT_URL_PREFIX = (
        "https://www.googleapis.com/service_accounts/v1/metadata/x509/"
    )

    try:
        token = client.verify_id_token(
            id_token=id_token,
            audience=os.environ["AUDIENCE"],
            cert_uri=PUBLIC_CERT_URL_PREFIX + CHAT_ISSUER,
        )
    except Exception:
        raise UnverifiedError("Invalid token")

    if token["iss"] != CHAT_ISSUER:
        raise UnverifiedError("Invalid issuee")

    return True


def generate_policy(
    event,
    principal_id: str,
    allow: bool,
    context: typing.Optional[typing.Dict[str, str]],
) -> typing.Dict[str, typing.Any]:

    policy = {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Allow" if allow else "Deny",
                    "Resource": event["methodArn"],
                },
            ],
        },
    }
    if context:
        policy["context"] = context

    logger.debug(policy)

    return policy


@tracer.capture_lambda_handler
def lambda_handler(event, context) -> typing.Dict[str, typing.Any]:
    logger.debug(event)

    token: str = event["authorizationToken"]

    context = {}
    if not token.startswith("Bearer "):
        verify = False
        context["message"] = "Authorization type is not Bearer"
    else:
        token = token.split(" ", 1)[1]
        try:
            verify = verify_token(token)
        except UnverifiedError as e:
            verify = False
            context["message"] = e.message

    return generate_policy(
        event,
        principal_id="gchat",
        allow=verify,
        context=context,
    )
