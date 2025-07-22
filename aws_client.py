"""
Base AWS client with error handling and retry logic.
Provides a robust foundation for AWS service interactions.
"""

import boto3
import time
from typing import Any, Optional
from botocore.exceptions import (
    ClientError,
    NoCredentialsError,
    PartialCredentialsError,
    EndpointConnectionError,
    ConnectTimeoutError,
    ReadTimeoutError,
)
from botocore.config import Config
from config_manager import config
from logger import logger


class AWSClientError(Exception):
    """Custom exception for AWS client errors."""

    pass


class AWSClient:
    """Base AWS client with error handling and retry logic."""

    def __init__(self, service_name: str, region: Optional[str] = None):
        self.service_name = service_name
        self.region = region or config.get("aws.region", "us-east-1")
        self.max_retries = config.get("aws.max_retries", 3)
        self.timeout = config.get("aws.timeout", 30)
        self.client = self._create_client()

    def _create_client(self) -> boto3.client:
        """Create AWS client with proper configuration."""
        try:
            session = boto3.Session(region_name=self.region)
            client_config = Config(
                retries=dict(max_attempts=self.max_retries),
                read_timeout=self.timeout,
                connect_timeout=self.timeout,
            )
            client = session.client(self.service_name, config=client_config)

            logger.info(
                f"AWS {self.service_name} client created successfully",
                region=self.region,
            )
            return client

        except NoCredentialsError:
            error_msg = (
                "AWS credentials not found. Please configure your AWS credentials."
            )
            logger.critical(error_msg)
            raise AWSClientError(error_msg)
        except PartialCredentialsError as e:
            error_msg = f"Incomplete AWS credentials: {e}"
            logger.critical(error_msg)
            raise AWSClientError(error_msg)
        except Exception as e:
            error_msg = f"Failed to create AWS {self.service_name} client: {e}"
            logger.critical(error_msg, exc_info=e)
            raise AWSClientError(error_msg)

    def _handle_aws_error(self, error: Exception, operation: str) -> str:
        """Handle AWS errors and return user-friendly messages."""
        if isinstance(error, ClientError):
            error_code = error.response["Error"]["Code"]
            error_message = error.response["Error"]["Message"]

            logger.log_aws_error(
                service=self.service_name,
                operation=operation,
                error=error,
                error_code=error_code,
                error_message=error_message,
            )

            if error_code == "AccessDenied":
                return f"Access denied to {self.service_name}. Please check your permissions."
            elif error_code == "NoSuchBucket":
                return "The specified S3 bucket does not exist."
            elif error_code == "NoSuchEntity":
                return "The specified IAM entity does not exist."
            elif error_code == "ThrottlingException":
                return "AWS API rate limit exceeded. Please try again later."
            elif error_code == "ServiceUnavailable":
                return f"AWS {self.service_name} service is temporarily unavailable."
            else:
                return f"AWS {self.service_name} error: {error_message}"

        elif isinstance(error, (EndpointConnectionError, ConnectTimeoutError)):
            error_msg = f"Connection to AWS {self.service_name} failed. Please check your internet connection."
            logger.log_aws_error(self.service_name, operation, error)
            return error_msg

        elif isinstance(error, ReadTimeoutError):
            error_msg = (
                f"Request to AWS {self.service_name} timed out. Please try again."
            )
            logger.log_aws_error(self.service_name, operation, error)
            return error_msg

        else:
            error_msg = f"Unexpected error with AWS {self.service_name}: {str(error)}"
            logger.log_aws_error(self.service_name, operation, error)
            return error_msg

    def execute_with_retry(self, operation: str, func, *args, **kwargs) -> Any:
        """Execute AWS operation with retry logic and error handling."""
        start_time = time.time()

        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(
                    f"Executing {operation} (attempt {attempt + 1}/{self.max_retries + 1})"
                )
                result = func(*args, **kwargs)

                duration = time.time() - start_time
                logger.log_tool_execution(
                    tool_name=f"{self.service_name}.{operation}",
                    success=True,
                    duration=duration,
                )

                return result

            except (
                ClientError,
                EndpointConnectionError,
                ConnectTimeoutError,
                ReadTimeoutError,
            ) as e:
                duration = time.time() - start_time

                if isinstance(e, ClientError):
                    error_code = e.response["Error"]["Code"]
                    if error_code in [
                        "AccessDenied",
                        "NoSuchBucket",
                        "NoSuchEntity",
                        "ValidationError",
                    ]:
                        logger.log_tool_execution(
                            tool_name=f"{self.service_name}.{operation}",
                            success=False,
                            duration=duration,
                        )
                        return self._handle_aws_error(e, operation)

                if attempt < self.max_retries:
                    wait_time = (2**attempt) * 1  # Exponential backoff
                    logger.warning(
                        f"Retrying {operation} in {wait_time}s (attempt {attempt + 1}/{self.max_retries + 1})",
                        error=str(e),
                    )
                    time.sleep(wait_time)
                else:
                    logger.log_tool_execution(
                        tool_name=f"{self.service_name}.{operation}",
                        success=False,
                        duration=duration,
                    )
                    return self._handle_aws_error(e, operation)

            except Exception as e:
                duration = time.time() - start_time
                logger.log_tool_execution(
                    tool_name=f"{self.service_name}.{operation}",
                    success=False,
                    duration=duration,
                )
                logger.error(f"Unexpected error in {operation}", exc_info=e)
                return f"An unexpected error occurred: {str(e)}"

    def test_connection(self) -> bool:
        """Test AWS connection and permissions."""
        try:
            if self.service_name == "s3":
                self.client.list_buckets()
            elif self.service_name == "iam":
                self.client.list_users()
            else:
                self.client.meta.service_model.service_name

            logger.info(f"AWS {self.service_name} connection test successful")
            return True

        except Exception as e:
            logger.error(f"AWS {self.service_name} connection test failed", exc_info=e)
            return False
