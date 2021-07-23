import os
import typing
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from enum import Enum

import boto3
import sentry_sdk
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver
from aws_lambda_powertools.logging import correlation_paths
from boto3.dynamodb.conditions import Key
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

tracer = Tracer()
logger = Logger()
app = ApiGatewayResolver()

sentry_dsn = os.environ.get("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[AwsLambdaIntegration()],
        traces_sample_rate=1.0,
    )


table_name = os.environ["TABLE_NAME"]
table = boto3.resource("dynamodb").Table(table_name)

reply_message = os.environ["REPLY_MESSAGE"]


class EventType(Enum):
    ADDED_TO_SPACE = "ADDED_TO_SPACE"
    REMOVED_FROM_SPACE = "REMOVED_FROM_SPACE"
    MESSAGE = "MESSAGE"
    CARD_CLICKED = "CARD_CLICKED"


class GoogleBot:
    def __init__(self) -> None:
        self._event_handlers: typing.Dict[EventType, typing.Callable] = {}

    def handle(
        self, event: typing.Dict[str, typing.Any]
    ) -> typing.Dict[str, typing.Any]:
        self.event = event
        return self._event_handlers[EventType(self.event["type"])]()

    def _event(self, event_type: EventType):
        def register_handler(func: typing.Callable) -> typing.Callable:
            self._event_handlers[event_type] = func
            return func

        return register_handler

    @property
    def added_to_space(self):
        return self._event(EventType.ADDED_TO_SPACE)

    @property
    def removed_from_space(self):
        return self._event(EventType.REMOVED_FROM_SPACE)

    @property
    def message(self):
        return self._event(EventType.MESSAGE)

    @property
    def card_clicked(self):
        return self._event(EventType.CARD_CLICKED)


bot = GoogleBot()


def generate_info_text(items: typing.List[typing.Dict[str, str]]) -> str:
    users_info = OrderedDict()
    for item in items:
        users_info[item["user"]] = {
            "time": datetime.fromisoformat(
                item["SK"].split("#")[-1].replace("Z", "+00:00")
            ),
            "name": item["displayName"],
            "action": item["action"],
        }

    info_list = []
    jst = timezone(timedelta(hours=9))
    for info in users_info.values():
        info_text = "* " + info["name"] + ": "
        if info["action"] == "lunchStart-1h":
            back_time = (info["time"] + timedelta(hours=1)).astimezone(jst)
            info_text += back_time.strftime("%H:%M") + " 頃戻ります"
        elif info["action"] == "lunchStart-30m":
            back_time = (info["time"] + timedelta(minutes=30)).astimezone(jst)
            info_text += back_time.strftime("%H:%M") + " 頃戻ります"
        elif info["action"] == "lunchEnd":
            info_text += "戻りました"
        info_list.append(info_text)

    return "\n".join(info_list)


@bot.added_to_space
def added_to_space():
    table.put_item(
        Item={
            "PK": "JoinedSpace",
            "SK": bot.event["space"]["name"],
            "displayName": bot.event["space"]["displayName"],
            "type": bot.event["space"]["type"],
        },
    )
    return {}


@bot.removed_from_space
def removed_from_space():
    res = table.query(
        KeyConditionExpression=Key("PK").eq(bot.event["space"]["name"]),
        ProjectionExpression="PK, SK",
    )
    for item in res["Items"]:
        table.delete_item(Key=item)
    table.delete_item(
        Key={
            "PK": "JoinedSpace",
            "SK": bot.event["space"]["name"],
        },
    )
    return {}


@bot.message
def message():
    if reply_message:
        return {"text": reply_message}
    return {}


@bot.card_clicked
def card_clicked():
    table.put_item(
        Item={
            "PK": bot.event["space"]["name"],
            "SK": "#".join(
                [
                    bot.event["message"]["name"],
                    datetime.utcnow().isoformat() + "Z",
                ]
            ),
            "user": bot.event["user"]["name"],
            "displayName": bot.event["user"]["displayName"],
            "action": bot.event["action"]["actionMethodName"],
        },
    )
    res = table.query(
        KeyConditionExpression=Key("PK").eq(bot.event["space"]["name"])
        & Key("SK").begins_with(bot.event["message"]["name"])
    )

    origial_card = bot.event["message"]["cards"][0]
    header = origial_card["header"]
    button_section = origial_card["sections"][-1]
    info_section = {
        "widgets": [
            {
                "textParagraph": {
                    "text": generate_info_text(res["Items"]),
                },
            },
        ],
    }
    card = {
        "header": header,
        "sections": [
            info_section,
            button_section,
        ],
    }
    return {
        "actionResponse": {
            "type": "UPDATE_MESSAGE",
        },
        "cards": [card],
    }


@app.post("/api/callback")
@tracer.capture_method
def post_handler():
    logger.debug(app.current_event.json_body)

    return bot.handle(app.current_event.json_body)


@logger.inject_lambda_context(
    correlation_id_path=correlation_paths.API_GATEWAY_REST,
)
@tracer.capture_lambda_handler
def lambda_handler(event, context) -> typing.Dict[str, typing.Any]:
    logger.debug(event)
    return app.resolve(event, context)
