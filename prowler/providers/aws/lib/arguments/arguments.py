from argparse import ArgumentTypeError, Namespace
from re import fullmatch, search

from prowler.providers.aws.aws_provider import AwsProvider
from prowler.providers.aws.config import ROLE_SESSION_NAME
from prowler.providers.aws.lib.arn.arn import arn_type


def init_parser(self):
    """Init the AWS Provider CLI parser"""
    aws_parser = self.subparsers.add_parser(
        "aws", parents=[self.common_providers_parser], help="AWS Provider"
    )
    # Authentication Methods
    aws_auth_subparser = aws_parser.add_argument_group("Authentication Modes")
    aws_auth_subparser.add_argument(
        "--profile",
        "-p",
        nargs="?",
        default=None,
        help="AWS profile to launch prowler with",
    )
    aws_auth_subparser.add_argument(
        "--role",
        "-R",
        nargs="?",
        default=None,
        help="ARN of the role to be assumed",
        # TODO: Pending ARN validation
    )
    aws_auth_subparser.add_argument(
        "--role-session-name",
        nargs="?",
        default=ROLE_SESSION_NAME,
        help="An identifier for the assumed role session. Defaults to ProwlerAssessmentSession",
        type=validate_role_session_name,
    )
    aws_auth_subparser.add_argument(
        "--mfa",
        action="store_true",
        help="IAM entity enforces MFA so you need to input the MFA ARN and the TOTP",
    )
    aws_auth_subparser.add_argument(
        "--session-duration",
        "-T",
        nargs="?",
        default=3600,
        type=validate_session_duration,
        help="Assumed role session duration in seconds, must be between 900 and 43200. Default: 3600",
        # TODO: Pending session duration validation
    )
    aws_auth_subparser.add_argument(
        "--external-id",
        "-I",
        nargs="?",
        default=None,
        help="External ID to be passed when assuming role",
    )
    # AWS Regions
    aws_regions_subparser = aws_parser.add_argument_group("AWS Regions")
    aws_regions_subparser.add_argument(
        "--region",
        "--filter-region",
        "-f",
        nargs="+",
        help="AWS region names to run Prowler against",
        choices=AwsProvider.get_regions(partition=None),
    )
    # AWS Organizations
    aws_orgs_subparser = aws_parser.add_argument_group("AWS Organizations")
    aws_orgs_subparser.add_argument(
        "--organizations-role",
        "-O",
        nargs="?",
        help="Specify AWS Organizations management role ARN to be assumed, to get Organization metadata",
    )
    # AWS Security Hub
    aws_security_hub_subparser = aws_parser.add_argument_group("AWS Security Hub")
    aws_security_hub_subparser.add_argument(
        "--security-hub",
        "-S",
        action="store_true",
        help="Send check output to AWS Security Hub and save json-asff outuput.",
    )
    aws_security_hub_subparser.add_argument(
        "--skip-sh-update",
        action="store_true",
        help="Skip updating previous findings of Prowler in Security Hub",
    )
    aws_security_hub_subparser.add_argument(
        "--send-sh-only-fails",
        action="store_true",
        help="Send only Prowler failed findings to SecurityHub",
    )
    # AWS Quick Inventory
    aws_quick_inventory_subparser = aws_parser.add_argument_group("Quick Inventory")
    aws_quick_inventory_subparser.add_argument(
        "--quick-inventory",
        "-i",
        action="store_true",
        help="Run Prowler Quick Inventory. The inventory will be stored in an output csv by default",
    )
    # AWS Outputs
    aws_outputs_subparser = aws_parser.add_argument_group("AWS Outputs to S3")
    aws_outputs_bucket_parser = aws_outputs_subparser.add_mutually_exclusive_group()
    aws_outputs_bucket_parser.add_argument(
        "--output-bucket",
        "-B",
        nargs="?",
        type=validate_bucket,
        default=None,
        help="Custom output bucket, requires -M <mode> and it can work also with -o flag.",
    )
    aws_outputs_bucket_parser.add_argument(
        "--output-bucket-no-assume",
        "-D",
        nargs="?",
        type=validate_bucket,
        default=None,
        help="Same as -B but do not use the assumed role credentials to put objects to the bucket, instead uses the initial credentials.",
    )

    # Based Scans
    aws_based_scans_subparser = aws_parser.add_argument_group("AWS Based Scans")
    aws_based_scans_parser = aws_based_scans_subparser.add_mutually_exclusive_group()
    aws_based_scans_parser.add_argument(
        "--resource-tag",
        "--resource-tags",
        nargs="+",
        default=None,
        help="Scan only resources with specific AWS Tags (Key=Value), e.g., Environment=dev Project=prowler",
    )
    aws_based_scans_parser.add_argument(
        "--resource-arn",
        "--resource-arns",
        nargs="+",
        type=arn_type,
        default=None,
        help="Scan only resources with specific AWS Resource ARNs, e.g., arn:aws:iam::012345678910:user/test arn:aws:ec2:us-east-1:123456789012:vpc/vpc-12345678",
    )

    # Boto3 Config
    boto3_config_subparser = aws_parser.add_argument_group("Boto3 Config")
    boto3_config_subparser.add_argument(
        "--aws-retries-max-attempts",
        nargs="?",
        default=None,
        type=int,
        help="Set the maximum attemps for the Boto3 standard retrier config (Default: 3)",
    )

    # Scan Unused Services
    scan_unused_services_subparser = aws_parser.add_argument_group(
        "Scan Unused Services"
    )
    scan_unused_services_subparser.add_argument(
        "--scan-unused-services",
        action="store_true",
        help="Scan unused services",
    )

    # Prowler Fixer
    prowler_fixer_subparser = aws_parser.add_argument_group("Prowler Fixer")
    prowler_fixer_subparser.add_argument(
        "--fixer",
        action="store_true",
        help="Fix the failed findings that can be fixed by Prowler",
    )


def validate_session_duration(session_duration: int) -> int:
    """validate_session_duration validates that the input session_duration is valid"""
    duration = int(session_duration)
    # Since the range(i,j) goes from i to j-1 we have to j+1
    if duration not in range(900, 43201):
        raise ArgumentTypeError(
            "Session duration must be between 900 and 43200 seconds"
        )
    else:
        return duration


def validate_role_session_name(session_name) -> str:
    """
    Validates that the role session name is valid.

    Args:
        session_name (str): The role session name to be validated.

    Returns:
        str: The validated role session name.

    Raises:
        ArgumentTypeError: If the role session name is invalid.

    Documentation:
        - AWS STS AssumeRole API: https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html
    """
    if fullmatch(r"[\w+=,.@-]{2,64}", session_name):
        return session_name
    else:
        raise ArgumentTypeError(
            "Role session name must be between 2 and 64 characters long and may contain alphanumeric characters, hyphens, underscores, plus signs, equal signs, commas, periods, at signs, and tildes."
        )


def validate_arguments(arguments: Namespace) -> tuple[bool, str]:
    """validate_arguments returns {True, "} if the provider arguments passed are valid and can be used together. It performs an extra validation, specific for the AWS provider, apart from the argparse lib."""

    # Handle if session_duration is not the default value or external_id is set
    if (
        (arguments.session_duration and arguments.session_duration != 3600)
        or arguments.external_id
        or arguments.role_session_name != ROLE_SESSION_NAME
    ):
        if not arguments.role:
            return (
                False,
                "To use -I/--external-id, -T/--session-duration or --role-session-name options -R/--role option is needed",
            )

    return (True, "")


def validate_bucket(bucket_name: str) -> str:
    """validate_bucket validates that the input bucket_name is valid"""
    if search(
        "^(?!^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$)(?!.*\.{2})(?!.*\.-)(?!.*-\.)(?!^xn--)(?!^sthree-)(?!^amzn-s3-demo-)(?!.*--table-s3$)[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$",
        bucket_name,
    ):
        return bucket_name
    else:
        raise ArgumentTypeError(
            "Bucket name must be valid (https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html)"
        )
