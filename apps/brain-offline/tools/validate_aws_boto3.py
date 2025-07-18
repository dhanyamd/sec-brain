import boto3
import botocore
import botocore.config
import botocore.exceptions


def get_aws_identity() -> None:
    """
    Fetch and log the identity information of the currently authenticated user.

    Returns:
        None
    """

    try:
        sts_client = boto3.client("sts")

        identity = sts_client.get_caller_identity()

        print("AWS Identity Information:")
        print(f"Account ID: {identity['Account']}")
        print(f"User ID: {identity['UserId']}")
        print(f"ARN: {identity['Arn']}")
    except botocore.exceptions.NoCredentialsError:
        print(
            "No AWS credentials were found. Make sure your environment is configured correctly."
        )
    except botocore.exceptions.PartialCredentialsError:
        print(
            "Incomplete AWS credentials were found. Ensure both Access Key and Secret Key are set."
        )
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    get_aws_identity()