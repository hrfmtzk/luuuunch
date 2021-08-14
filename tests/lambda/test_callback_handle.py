import json
import os
import sys
import typing
from dataclasses import dataclass
from pathlib import Path

import pytest
from moto import mock_cloudwatch, mock_dynamodb2
from pytest_mock import MockerFixture


class TestGenerateInfoText:
    @pytest.fixture(scope="function")
    def env(self) -> None:
        os.environ["AWS_ACCESS_KEY_ID"] = "testing"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
        os.environ["AWS_SECURITY_TOKEN"] = "testing"
        os.environ["AWS_SESSION_TOKEN"] = "testing"
        os.environ["TABLE_NAME"] = "TestLuuuunch"
        os.environ["REPLY_MESSAGE"] = ""
        os.environ["POWERTOOLS_TRACE_DISABLED"] = "true"

    @pytest.fixture
    def target(self, env):
        root_dir = Path(__file__).resolve().parents[2]

        original_path = sys.path
        original_modules = sys.modules
        sys.path.append(str(root_dir))
        from src.callback_handle.index import generate_info_text

        with mock_cloudwatch(), mock_dynamodb2():
            yield generate_info_text

        sys.path = original_path
        sys.modules = original_modules

    @pytest.mark.parametrize(
        argnames=["items", "expect"],
        argvalues=[
            (
                [],
                "",
            ),
            (
                [
                    {
                        "PK": "spaces/AAAAAA",
                        "SK": "spaces/AAAAAA/messages/xxxxxx#2000-01-01T00:00:00.000Z",  # noqa
                        "user": "users/0001",
                        "displayName": "John Doe",
                        "action": "lunchStart-1h",
                    },
                ],
                "* John Doe: 10:00 頃戻ります",
            ),
            (
                [
                    {
                        "PK": "spaces/AAAAAA",
                        "SK": "spaces/AAAAAA/messages/xxxxxx#2000-01-01T00:00:00.000Z",  # noqa
                        "user": "users/0001",
                        "displayName": "John Doe",
                        "action": "lunchStart-30m",
                    },
                ],
                "* John Doe: 09:30 頃戻ります",
            ),
            (
                [
                    {
                        "PK": "spaces/AAAAAA",
                        "SK": "spaces/AAAAAA/messages/xxxxxx#2000-01-01T00:00:00.000Z",  # noqa
                        "user": "users/0001",
                        "displayName": "John Doe",
                        "action": "lunchStart-1h",
                    },
                    {
                        "PK": "spaces/AAAAAA",
                        "SK": "spaces/AAAAAA/messages/xxxxxx#2000-01-01T01:00:00.000Z",  # noqa
                        "user": "users/0001",
                        "displayName": "John Doe",
                        "action": "lunchEnd",
                    },
                ],
                "* John Doe: 戻りました",
            ),
        ],
    )
    def test_generate_info_text(self, target, items, expect) -> None:
        info_text = target(items)

        assert info_text == expect


@dataclass
class LambdaContext:
    function_name: str = "test"
    memory_limit_in_mb: int = 128
    invoked_function_arn: str = (
        "arn:aws:lambda:eu-west-1:809313241:function:test"
    )
    aws_request_id: str = "52fdfc07-2182-154f-163f-5f0f9a621d72"


class TestHandler:
    @pytest.fixture
    def target(self):
        root_dir = Path(__file__).resolve().parents[2]
        sys.path.append(str(root_dir))
        os.environ["TABLE_NAME"] = "TestLuuuunch"
        os.environ["REPLY_MESSAGE"] = ""
        os.environ["POWERTOOLS_TRACE_DISABLED"] = "true"
        from src.callback_handle.index import lambda_handler

        return lambda_handler

    @pytest.fixture
    def lambda_context(self) -> LambdaContext:
        return LambdaContext()

    def create_post_event(
        self, json_body: typing.Dict[str, typing.Any]
    ) -> typing.Dict[str, typing.Any]:
        return {
            "resource": "/api/callback",
            "path": "/api/callback",
            "httpMethod": "POST",
            "headers": {
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",  # noqa
                "accept-encoding": "gzip, deflate, br",
                "accept-language": "en-US,en;q=0.9",
                "cookie": "s_fid=7AAB6XMPLAFD9BBF-0643XMPL09956DE2; regStatus=pre-register",  # noqa
                "Host": "70ixmpl4fl.execute-api.us-east-2.amazonaws.com",
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "none",
                "upgrade-insecure-requests": "1",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36",  # noqa
                "X-Amzn-Trace-Id": "Root=1-5e66d96f-7491f09xmpl79d18acf3d050",
                "X-Forwarded-For": "52.255.255.12",
                "X-Forwarded-Port": "443",
                "X-Forwarded-Proto": "https",
            },
            "multiValueHeaders": {
                "accept": [
                    "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"  # noqa
                ],
                "accept-encoding": ["gzip, deflate, br"],
                "accept-language": ["en-US,en;q=0.9"],
                "cookie": [
                    "s_fid=7AABXMPL1AFD9BBF-0643XMPL09956DE2; regStatus=pre-register;"  # noqa
                ],
                "Host": ["70ixmpl4fl.execute-api.ca-central-1.amazonaws.com"],
                "sec-fetch-dest": ["document"],
                "sec-fetch-mode": ["navigate"],
                "sec-fetch-site": ["none"],
                "upgrade-insecure-requests": ["1"],
                "User-Agent": [
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36"  # noqa
                ],
                "X-Amzn-Trace-Id": ["Root=1-5e66d96f-7491f09xmpl79d18acf3d050"],
                "X-Forwarded-For": ["52.255.255.12"],
                "X-Forwarded-Port": ["443"],
                "X-Forwarded-Proto": ["https"],
            },
            "queryStringParameters": {},
            "multiValueQueryStringParameters": {},
            "pathParameters": {},
            "stageVariables": None,
            "requestContext": {
                "resourceId": "2gxmpl",
                "resourcePath": "/api/callback",
                "httpMethod": "POST",
                "extendedRequestId": "JJbxmplHYosFVYQ=",
                "requestTime": "10/Mar/2020:00:03:59 +0000",
                "path": "/api/callback",
                "accountId": "123456789012",
                "protocol": "HTTP/1.1",
                "stage": "Prod",
                "domainPrefix": "70ixmpl4fl",
                "requestTimeEpoch": 1583798639428,
                "requestId": "77375676-xmpl-4b79-853a-f982474efe18",
                "identity": {
                    "cognitoIdentityPoolId": None,
                    "accountId": None,
                    "cognitoIdentityId": None,
                    "caller": None,
                    "sourceIp": "52.255.255.12",
                    "principalOrgId": None,
                    "accessKey": None,
                    "cognitoAuthenticationType": None,
                    "cognitoAuthenticationProvider": None,
                    "userArn": None,
                    "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36",  # noqa
                    "user": None,
                },
                "domainName": "70ixmpl4fl.execute-api.us-east-2.amazonaws.com",
                "apiId": "70ixmpl4fl",
            },
            "body": json.dumps(json_body),
            "isBase64Encoded": False,
        }

    def assert_response(
        self,
        response: typing.Dict[str, typing.Any],
        status_code: int,
        body: typing.Dict[str, typing.Any],
    ) -> None:
        assert response["statusCode"] == status_code
        assert json.loads(response["body"]) == body

    def test_added_to_space(
        self, mocker: MockerFixture, lambda_context: LambdaContext, target
    ) -> None:
        lambda_event = self.create_post_event(
            {
                "type": "ADDED_TO_SPACE",
                "eventTime": "2017-03-02T19:02:59.910959Z",
                "space": {
                    "name": "spaces/AAAAAAAAAAA",
                    "displayName": "Chuck Norris Discussion Room",
                    "type": "ROOM",
                },
                "user": {
                    "name": "users/12345678901234567890",
                    "displayName": "Chuck Norris",
                    "avatarUrl": "https://lh3.googleusercontent.com/.../photo.jpg",  # noqa
                    "email": "chuck@example.com",
                },
            }
        )
        expected_response = {}

        mocker.patch(
            "src.callback_handle.index.table",
            put_item=mocker.Mock(),
        )
        response = target(lambda_event, lambda_context)

        self.assert_response(response, 200, expected_response)

    def test_removed_from_space(
        self, mocker: MockerFixture, lambda_context: LambdaContext, target
    ) -> None:
        lambda_event = self.create_post_event(
            {
                "type": "REMOVED_FROM_SPACE",
                "eventTime": "2017-03-02T19:02:59.910959Z",
                "space": {
                    "name": "spaces/AAAAAAAAAAA",
                    "type": "DM",
                },
                "user": {
                    "name": "users/12345678901234567890",
                    "displayName": "Chuck Norris",
                    "avatarUrl": "https://lh3.googleusercontent.com/.../photo.jpg",  # noqa
                    "email": "chuck@example.com",
                },
            }
        )
        expected_response = {}

        mocker.patch(
            "src.callback_handle.index.table",
            query=mocker.Mock(return_value={"Items": []}),
            delete_item=mocker.Mock(),
        )
        response = target(lambda_event, lambda_context)

        self.assert_response(response, 200, expected_response)

    def test_message(
        self, mocker: MockerFixture, lambda_context: LambdaContext, target
    ) -> None:
        lambda_event = self.create_post_event(
            {
                "type": "MESSAGE",
                "eventTime": "2017-03-02T19:02:59.910959Z",
                "space": {
                    "name": "spaces/AAAAAAAAAAA",
                    "displayName": "Chuck Norris Discussion Room",
                    "type": "ROOM",
                },
                "message": {
                    "name": "spaces/AAAAAAAAAAA/messages/CCCCCCCCCCC",
                    "sender": {
                        "name": "users/12345678901234567890",
                        "displayName": "Chuck Norris",
                        "avatarUrl": "https://lh3.googleusercontent.com/.../photo.jpg",  # noqa
                        "email": "chuck@example.com",
                    },
                    "createTime": "2017-03-02T19:02:59.910959Z",
                    "text": "@TestBot Violence is my last option.",
                    "argumentText": " Violence is my last option.",
                    "thread": {
                        "name": "spaces/AAAAAAAAAAA/threads/BBBBBBBBBBB",
                    },
                    "annotations": [
                        {
                            "length": 8,
                            "startIndex": 0,
                            "userMention": {
                                "type": "MENTION",
                                "user": {
                                    "avatarUrl": "https://.../avatar.png",
                                    "displayName": "TestBot",
                                    "name": "users/1234567890987654321",
                                    "type": "BOT",
                                },
                            },
                            "type": "USER_MENTION",
                        }
                    ],
                    "attachment": [
                        {
                            "name": "spaces/5o6pDgAAAAE/messages/Ohu1LlUVcS8.Ohu1LlUVcS8/attachments/AATUf-Iz7d8kySEdRRZd-dznqBk3",  # noqa
                            "content_name": "solar.png",
                            "content_type": "image/png",
                            "drive_data_ref": {
                                "drive_file_id": "H1HqaqRuH2Pfd_TOa1fF2_ltwDlV_yKRrr",  # noqa
                            },
                            "source": "DRIVE_FILE",
                        }
                    ],
                },
                "user": {
                    "name": "users/12345678901234567890",
                    "displayName": "Chuck Norris",
                    "avatarUrl": "https://lh3.googleusercontent.com/.../photo.jpg",  # noqa
                    "email": "chuck@example.com",
                },
            }
        )
        expected_response = {}

        response = target(lambda_event, lambda_context)

        self.assert_response(response, 200, expected_response)

    def test_card_clicked_lunch_start(
        self, mocker: MockerFixture, lambda_context: LambdaContext, target
    ) -> None:
        lambda_event = self.create_post_event(
            {
                "type": "CARD_CLICKED",
                "eventTime": "2017-11-14T01:44:58.521823Z",
                "message": {
                    "name": "spaces/AAAAtZLKDkk/messages/e3fCf-i1PXE.8OGDcWT2HwI",  # noqa
                    "sender": {
                        "name": "users/118066814328248020034",
                        "displayName": "Test Bot",
                        "avatarUrl": "https://lh6.googleusercontent.com/...",
                        "type": "BOT",
                    },
                    "createTime": "2017-11-14T01:44:58.521823Z",
                    "space": {
                        "name": "spaces/AAAAtZLKDkk",
                        "type": "ROOM",
                        "displayName": "Testing Room",
                    },
                    "thread": {
                        "name": "spaces/AAAAtZLKDkk/threads/e3fCf-i1PXE",
                        "retentionSettings": {},
                    },
                    "cards": [
                        {
                            "header": {"title": "Luuuunch!!!!"},
                            "sections": [
                                {
                                    "widgets": [
                                        {
                                            "buttons": [
                                                {
                                                    "textButton": {
                                                        "text": "Start",
                                                        "onClick": {
                                                            "action": {
                                                                "actionMethodName": "lunchStart",  # noqa
                                                            }
                                                        },
                                                    }
                                                },
                                                {
                                                    "textButton": {
                                                        "text": "End",
                                                        "onClick": {
                                                            "action": {
                                                                "actionMethodName": "lunchEnd",  # noqa
                                                            }
                                                        },
                                                    }
                                                },
                                            ]
                                        }
                                    ]
                                }
                            ],
                        }
                    ],
                },
                "user": {
                    "name": "users/102651148563033885715",
                    "displayName": "Geordi La Forge",
                    "avatarUrl": "https://dev2-lighthouse.sandbox.google.com/...",  # noqa
                    "type": "HUMAN",
                },
                "space": {
                    "name": "spaces/AAAAtZLKDkk",
                    "type": "ROOM",
                    "displayName": "Testing Room",
                },
                "action": {
                    "actionMethodName": "lunchStart",
                    "parameters": [],
                },
            }
        )
        expected_response = {
            "actionResponse": {
                "type": "UPDATE_MESSAGE",
            },
            "cards": [
                {
                    "header": {"title": "Luuuunch!!!!"},
                    "sections": [
                        {
                            "widgets": [
                                {
                                    "textParagraph": {
                                        "text": "",
                                    },
                                },
                            ],
                        },
                        {
                            "widgets": [
                                {
                                    "buttons": [
                                        {
                                            "textButton": {
                                                "text": "Start",
                                                "onClick": {
                                                    "action": {
                                                        "actionMethodName": "lunchStart",  # noqa
                                                    }
                                                },
                                            }
                                        },
                                        {
                                            "textButton": {
                                                "text": "End",
                                                "onClick": {
                                                    "action": {
                                                        "actionMethodName": "lunchEnd",  # noqa
                                                    }
                                                },
                                            }
                                        },
                                    ]
                                }
                            ]
                        },
                    ],
                }
            ],
        }

        mocker.patch(
            "src.callback_handle.index.table",
            put_item=mocker.Mock(),
            query=mocker.Mock(return_value={"Items": []}),
        )
        response = target(lambda_event, lambda_context)

        self.assert_response(response, 200, expected_response)
