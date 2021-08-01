import typing

from aws_cdk import (
    aws_apigateway as apigateway,
    aws_certificatemanager as acm,
    aws_dynamodb as dynamodb,
    aws_events as events,
    aws_events_targets as events_targets,
    aws_lambda as lambda_,
    aws_lambda_python as lambda_python,
    aws_secretsmanager as secretsmanager,
    core as cdk,
)


class LuuuunchNotification(cdk.Construct):
    def __init__(
        self,
        scope: cdk.Construct,
        id: str,
        secret: secretsmanager.Secret,
        table: dynamodb.Table,
        icon_url: str,
        log_level: str,
        sentry_dsn: typing.Optional[str] = None,
    ) -> None:
        super().__init__(scope, id)

        sentry_dsn = sentry_dsn or ""

        function = lambda_python.PythonFunction(
            self,
            "Function",
            entry="src/notification",
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_8,
            environment={
                "SECRET_ID": secret.secret_arn,
                "TABLE_NAME": table.table_name,
                "ICON_URL": icon_url,
                "LOG_LEVEL": log_level,
                "POWERTOOLS_SERVICE_NAME": "luuuunch",
                "SENTRY_DSN": sentry_dsn,
            },
        )
        secret.grant_read(function)
        table.grant_read_data(function)

        rule = events.Rule(
            self,
            "Rule",
            schedule=events.Schedule.cron(  # every weekday 12:00
                week_day="MON-FRI",
                hour="3",
                minute="0",
            ),
        )
        rule.add_target(events_targets.LambdaFunction(handler=function))


class LuuuunchCallback(cdk.Construct):
    def __init__(
        self,
        scope: cdk.Construct,
        id: str,
        project_id: str,
        table: dynamodb.Table,
        log_level: str,
        reply_message: typing.Optional[str] = None,
        certificate_arn: typing.Optional[str] = None,
        domain_name: typing.Optional[str] = None,
        sentry_dsn: typing.Optional[str] = None,
    ) -> None:
        super().__init__(scope, id)

        sentry_dsn = sentry_dsn or ""
        if domain_name and not certificate_arn:
            raise ValueError(
                "`CERTIFICATE_ARN` is required when using custom domain"
            )

        api = apigateway.RestApi(
            self,
            "RestApi",
        )
        if domain_name and certificate_arn:
            api.add_domain_name(
                "DomainName",
                certificate=acm.Certificate.from_certificate_arn(
                    self,
                    "Certificate",
                    certificate_arn=certificate_arn,
                ),
                domain_name=domain_name,
                endpoint_type=apigateway.EndpointType.EDGE,
                security_policy=apigateway.SecurityPolicy.TLS_1_2,
            )

        api_resource = api.root.add_resource("api")
        callback_resource = api_resource.add_resource("callback")

        handle_function = lambda_python.PythonFunction(
            self,
            "HandleFunction",
            entry="src/callback_handle",
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_8,
            environment={
                "TABLE_NAME": table.table_name,
                "REPLY_MESSAGE": reply_message or "",
                "LOG_LEVEL": log_level,
                "POWERTOOLS_SERVICE_NAME": "luuuunch",
                "SENTRY_DSN": sentry_dsn,
            },
        )
        table.grant_full_access(handle_function)

        auth_function = lambda_python.PythonFunction(
            self,
            "AuthFunction",
            entry="src/callback_auth",
            index="index.py",
            handler="lambda_handler",
            runtime=lambda_.Runtime.PYTHON_3_8,
            environment={
                "AUDIENCE": project_id,
                "LOG_LEVEL": log_level,
                "POWERTOOLS_SERVICE_NAME": "luuuunch",
                "SENTRY_DSN": sentry_dsn,
            },
        )

        callback_resource.add_method(
            http_method="POST",
            integration=apigateway.LambdaIntegration(
                handler=handle_function,
            ),
            authorizer=apigateway.TokenAuthorizer(
                self,
                "TokenAuthorizer",
                handler=auth_function,
            ),
        )


class LuuuunchStack(cdk.Stack):
    def __init__(
        self,
        scope: cdk.Construct,
        construct_id: str,
        icon_url: str,
        project_id: str,
        reply_message: typing.Optional[str] = None,
        certificate_arn: typing.Optional[str] = None,
        domain_name: typing.Optional[str] = None,
        log_level: typing.Optional[str] = None,
        sentry_dsn: typing.Optional[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        log_level = log_level or "INFO"

        secret = secretsmanager.Secret(
            self,
            "Secret",
            description="luuuunch service account credential",
        )
        table = dynamodb.Table(
            self,
            "Table",
            table_name="luuuunch",
            partition_key=dynamodb.Attribute(
                name="PK",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="SK",
                type=dynamodb.AttributeType.STRING,
            ),
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
        )

        LuuuunchNotification(
            self,
            "Notification",
            secret=secret,
            table=table,
            icon_url=icon_url,
            log_level=log_level,
            sentry_dsn=sentry_dsn,
        )

        LuuuunchCallback(
            self,
            "Callback",
            project_id=project_id,
            table=table,
            log_level=log_level,
            reply_message=reply_message,
            certificate_arn=certificate_arn,
            domain_name=domain_name,
            sentry_dsn=sentry_dsn,
        )
