"""
S3 tools for AWS Assistant.
Provides tools for S3 bucket operations.
"""

from langchain_core.tools import tool
from aws_client import AWSClient
from logger import logger


class S3Client(AWSClient):
    """S3 client with specialized operations."""

    def __init__(self, region: str = None):
        super().__init__("s3", region)

    def list_buckets(self):
        """List all S3 buckets."""
        return self.execute_with_retry("list_buckets", self.client.list_buckets)

    def get_bucket_acl(self, bucket_name: str):
        """Get bucket ACL."""
        return self.execute_with_retry(
            "get_bucket_acl", self.client.get_bucket_acl, Bucket=bucket_name
        )

    def list_objects_v2(self, bucket_name: str, **kwargs):
        """List objects in bucket."""
        return self.execute_with_retry(
            "list_objects_v2", self.client.list_objects_v2, Bucket=bucket_name, **kwargs
        )


# Global S3 client instance - will be initialized when needed
s3_client = None


def _get_s3_client():
    """Get or create S3 client instance."""
    global s3_client
    if s3_client is None:
        s3_client = S3Client()
    return s3_client


@tool
def list_s3_buckets() -> str:
    """
    Returns a list of all S3 buckets in the AWS account.
    """
    try:
        logger.info("Executing list_s3_buckets tool")
        client = _get_s3_client()
        response = client.list_buckets()

        if isinstance(response, str):  # Error response
            return response

        bucket_names = [bucket["Name"] for bucket in response.get("Buckets", [])]

        if not bucket_names:
            return "No S3 buckets found in your AWS account."

        return f"S3 buckets: {', '.join(bucket_names)}."

    except Exception as e:
        logger.error("Error in list_s3_buckets", exc_info=e)
        return f"Failed to list S3 buckets: {str(e)}"


@tool
def list_public_s3_buckets() -> str:
    """
    Returns a list of S3 buckets that are publicly accessible.
    """
    try:
        logger.debug("Executing list_public_s3_buckets tool")

        # First, get all buckets
        client = _get_s3_client()
        response = client.list_buckets()

        if isinstance(response, str):  # Error response
            return response

        buckets = response.get("Buckets", [])
        public_buckets = []

        for bucket in buckets:
            bucket_name = bucket["Name"]
            try:
                # Check bucket ACL for public access
                acl_response = client.get_bucket_acl(bucket_name)

                if isinstance(acl_response, str):  # Error response
                    logger.warning(
                        f"Could not check ACL for bucket {bucket_name}: {acl_response}"
                    )
                    continue

                # Check if bucket is publicly accessible
                for grant in acl_response.get("Grants", []):
                    grantee = grant.get("Grantee", {})
                    if (
                        grantee.get("URI")
                        == "http://acs.amazonaws.com/groups/global/AllUsers"
                    ):
                        public_buckets.append(bucket_name)
                        break

            except Exception as e:
                logger.warning(f"Error checking bucket {bucket_name} ACL: {e}")
                continue

        if not public_buckets:
            return "No publicly accessible S3 buckets found."

        return f"Public S3 buckets: {', '.join(public_buckets)}."

    except Exception as e:
        logger.error("Error in list_public_s3_buckets", exc_info=e)
        return f"Failed to list public S3 buckets: {str(e)}"


@tool
def inspect_s3_bucket(bucket_name: str) -> str:
    """
    Lists the contents of a specified S3 bucket.

    Args:
        bucket_name: The name of the S3 bucket to inspect
    """
    try:
        logger.debug(f"Executing inspect_s3_bucket tool for bucket: {bucket_name}")

        # Validate bucket name
        if not bucket_name or not bucket_name.strip():
            return "Please provide a valid bucket name."

        bucket_name = bucket_name.strip()

        # List objects in the bucket
        client = _get_s3_client()
        response = client.list_objects_v2(
            bucket_name, MaxKeys=100
        )  # Limit to 100 objects

        if isinstance(response, str):  # Error response
            return response

        objects = response.get("Contents", [])

        if not objects:
            return f"The bucket '{bucket_name}' is empty."

        # Extract object names
        object_names = [obj["Key"] for obj in objects]

        # If there are more objects, indicate this
        if response.get("IsTruncated", False):
            return f"The bucket '{bucket_name}' contains {len(object_names)} objects (showing first 100): {', '.join(object_names)}."
        else:
            return f"The bucket '{bucket_name}' contains: {', '.join(object_names)}."

    except Exception as e:
        logger.error(f"Error in inspect_s3_bucket for bucket {bucket_name}", exc_info=e)
        return f"Failed to inspect bucket '{bucket_name}': {str(e)}"


@tool
def get_s3_bucket_info(bucket_name: str) -> str:
    """
    Gets detailed information about a specific S3 bucket including size, object count, and creation date.

    Args:
        bucket_name: The name of the S3 bucket to get information about
    """
    try:
        logger.debug(f"Executing get_s3_bucket_info tool for bucket: {bucket_name}")

        if not bucket_name or not bucket_name.strip():
            return "Please provide a valid bucket name."

        bucket_name = bucket_name.strip()

        client = _get_s3_client()
        bucket_response = client.list_buckets()

        if isinstance(bucket_response, str):
            return bucket_response

        bucket_info = None
        for bucket in bucket_response.get("Buckets", []):
            if bucket["Name"] == bucket_name:
                bucket_info = bucket
                break

        if not bucket_info:
            return f"Bucket '{bucket_name}' not found."

        objects_response = client.list_objects_v2(bucket_name)

        if isinstance(objects_response, str):
            return f"Bucket '{bucket_name}' found, but could not retrieve object information: {objects_response}"

        objects = objects_response.get("Contents", [])
        total_size = sum(obj.get("Size", 0) for obj in objects)

        if total_size < 1024:
            size_str = f"{total_size} bytes"
        elif total_size < 1024 * 1024:
            size_str = f"{total_size / 1024:.1f} KB"
        elif total_size < 1024 * 1024 * 1024:
            size_str = f"{total_size / (1024 * 1024):.1f} MB"
        else:
            size_str = f"{total_size / (1024 * 1024 * 1024):.1f} GB"

        creation_date = bucket_info["CreationDate"].strftime("%Y-%m-%d %H:%M:%S UTC")

        return (
            f"Bucket '{bucket_name}' information:\n"
            f"- Creation date: {creation_date}\n"
            f"- Object count: {len(objects)}\n"
            f"- Total size: {size_str}"
        )

    except Exception as e:
        logger.error(
            f"Error in get_s3_bucket_info for bucket {bucket_name}", exc_info=e
        )
        return f"Failed to get information for bucket '{bucket_name}': {str(e)}"
