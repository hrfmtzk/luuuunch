import json
import os

import aws_cdk as cdk
import pytest
from aws_cdk import assertions
from pytest_snapshot.plugin import Snapshot

from luuuunch.luuuunch_stack import LuuuunchStack
from tests.helpers import ignore_template_assets


class TestApp:
    @pytest.fixture(scope="function")
    def environ(self) -> None:
        os.environ["AWS_ACCESS_KEY_ID"] = "testing"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
        os.environ["AWS_SECURITY_TOKEN"] = "testing"
        os.environ["AWS_SESSION_TOKEN"] = "testing"

    @pytest.fixture(scope="function")
    def app(self, environ) -> cdk.App:
        return cdk.App()

    @pytest.fixture(scope="function")
    def env(self, app: cdk.App) -> cdk.Environment:
        return cdk.Environment(
            account=app.account,
            region=app.region,
        )

    def test_luuuunch_stack_snapshot(
        self, snapshot: Snapshot, app: cdk.App, env: cdk.Environment
    ) -> None:
        stack = LuuuunchStack(
            app,
            "Luuuunch",
            icon_url="https://example.com/icon.png",
            project_id="99999999",
            reply_message="hello world!",
            certificate_arn="arn:aws:acm:us-east-1:123456789012:certificate/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",  # noqa
            domain_name="example.com",
            log_level="DEBUG",
            sentry_dsn="https://xxxxxxxx.ingest.sentry.io/99999999",
            env=env,
        )

        template_json = ignore_template_assets(
            assertions.Template.from_stack(stack).to_json()
        )

        snapshot.assert_match(
            json.dumps(template_json, indent=2),
            "luuuunch_stack.json",
        )
