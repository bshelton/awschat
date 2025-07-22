"""
IAM tools for AWS Assistant.
Provides tools for IAM operations.
"""

from langchain_core.tools import tool
from aws_client import AWSClient
from logger import logger


class IAMClient(AWSClient):
    """IAM client with specialized operations."""

    def __init__(self, region: str = None):
        super().__init__("iam", region)

    def list_users(self):
        """List all IAM users."""
        return self.execute_with_retry("list_users", self.client.list_users)

    def list_groups(self):
        """List all IAM groups."""
        return self.execute_with_retry("list_groups", self.client.list_groups)

    def list_policies(self):
        """List all IAM policies."""
        return self.execute_with_retry("list_policies", self.client.list_policies)

    def list_roles(self):
        """List all IAM roles."""
        return self.execute_with_retry("list_roles", self.client.list_roles)

    def get_user(self, username: str):
        """Get specific IAM user details."""
        return self.execute_with_retry(
            "get_user", self.client.get_user, UserName=username
        )

    def list_user_groups(self, username: str):
        """List groups for a specific user."""
        return self.execute_with_retry(
            "list_groups_for_user", self.client.list_groups_for_user, UserName=username
        )

    def list_user_policies(self, username: str):
        """List inline policies for a specific user."""
        return self.execute_with_retry(
            "list_user_policies", self.client.list_user_policies, UserName=username
        )

    def list_attached_user_policies(self, username: str):
        """List attached policies for a specific user."""
        return self.execute_with_retry(
            "list_attached_user_policies",
            self.client.list_attached_user_policies,
            UserName=username,
        )


# Global IAM client instance - will be initialized when needed
iam_client = None


def _get_iam_client():
    """Get or create IAM client instance."""
    global iam_client
    if iam_client is None:
        iam_client = IAMClient()
    return iam_client


@tool
def list_iam_users() -> str:
    """
    Returns a list of all IAM users in the AWS account.
    """
    try:
        logger.debug("Executing list_iam_users tool")
        client = _get_iam_client()
        response = client.list_users()

        if isinstance(response, str):  # Error response
            return response

        users = response.get("Users", [])

        if not users:
            return "No IAM users found in your AWS account."

        user_names = [user["UserName"] for user in users]
        return f"IAM users: {', '.join(user_names)}."

    except Exception as e:
        logger.error("Error in list_iam_users", exc_info=e)
        return f"Failed to list IAM users: {str(e)}"


@tool
def list_iam_groups() -> str:
    """
    Returns a list of all IAM groups in the AWS account.
    """
    try:
        logger.debug("Executing list_iam_groups tool")
        client = _get_iam_client()
        response = client.list_groups()

        if isinstance(response, str):  # Error response
            return response

        groups = response.get("Groups", [])

        if not groups:
            return "No IAM groups found in your AWS account."

        group_names = [group["GroupName"] for group in groups]
        return f"IAM groups: {', '.join(group_names)}."

    except Exception as e:
        logger.error("Error in list_iam_groups", exc_info=e)
        return f"Failed to list IAM groups: {str(e)}"


@tool
def list_iam_policies() -> str:
    """
    Returns a list of all IAM policies in the AWS account.
    """
    try:
        logger.debug("Executing list_iam_policies tool")
        client = _get_iam_client()
        response = client.list_policies()

        if isinstance(response, str):  # Error response
            return response

        policies = response.get("Policies", [])

        if not policies:
            return "No IAM policies found in your AWS account."

        policy_names = [policy["PolicyName"] for policy in policies]
        return f"IAM policies: {', '.join(policy_names)}."

    except Exception as e:
        logger.error("Error in list_iam_policies", exc_info=e)
        return f"Failed to list IAM policies: {str(e)}"


@tool
def list_iam_roles() -> str:
    """
    Returns a list of all IAM roles in the AWS account.
    """
    try:
        logger.debug("Executing list_iam_roles tool")
        client = _get_iam_client()
        response = client.list_roles()

        if isinstance(response, str):  # Error response
            return response

        roles = response.get("Roles", [])

        if not roles:
            return "No IAM roles found in your AWS account."

        role_names = [role["RoleName"] for role in roles]
        return f"IAM roles: {', '.join(role_names)}."

    except Exception as e:
        logger.error("Error in list_iam_roles", exc_info=e)
        return f"Failed to list IAM roles: {str(e)}"


@tool
def get_iam_user_details(username: str) -> str:
    """
    Gets detailed information about a specific IAM user including groups and policies.

    Args:
        username: The name of the IAM user to get details for
    """
    try:
        logger.debug(f"Executing get_iam_user_details tool for user: {username}")

        # Validate username
        if not username or not username.strip():
            return "Please provide a valid username."

        username = username.strip()

        # Get user details
        client = _get_iam_client()
        user_response = client.get_user(username)

        if isinstance(user_response, str):  # Error response
            return user_response

        user = user_response.get("User", {})

        # Get user groups
        groups_response = client.list_user_groups(username)
        groups = []
        if not isinstance(groups_response, str):  # Not an error
            groups = [group["GroupName"] for group in groups_response.get("Groups", [])]

        # Get inline policies
        inline_policies_response = client.list_user_policies(username)
        inline_policies = []
        if not isinstance(inline_policies_response, str):  # Not an error
            inline_policies = inline_policies_response.get("PolicyNames", [])

        # Get attached policies
        attached_policies_response = client.list_attached_user_policies(username)
        attached_policies = []
        if not isinstance(attached_policies_response, str):  # Not an error
            attached_policies = [
                policy["PolicyName"]
                for policy in attached_policies_response.get("AttachedPolicies", [])
            ]

        # Format response
        result = [f"User '{username}' details:"]

        if user.get("CreateDate"):
            result.append(
                f"- Created: {user['CreateDate'].strftime('%Y-%m-%d %H:%M:%S UTC')}"
            )

        if user.get("PasswordLastUsed"):
            result.append(
                f"- Last password use: {user['PasswordLastUsed'].strftime('%Y-%m-%d %H:%M:%S UTC')}"
            )

        if groups:
            result.append(f"- Groups: {', '.join(groups)}")
        else:
            result.append("- Groups: None")

        if inline_policies:
            result.append(f"- Inline policies: {', '.join(inline_policies)}")
        else:
            result.append("- Inline policies: None")

        if attached_policies:
            result.append(f"- Attached policies: {', '.join(attached_policies)}")
        else:
            result.append("- Attached policies: None")

        return "\n".join(result)

    except Exception as e:
        logger.error(f"Error in get_iam_user_details for user {username}", exc_info=e)
        return f"Failed to get details for user '{username}': {str(e)}"


@tool
def search_iam_users(search_term: str) -> str:
    """
    Searches for IAM users that match the given search term.

    Args:
        search_term: The search term to match against user names
    """
    try:
        logger.debug(f"Executing search_iam_users tool with search term: {search_term}")

        # Validate search term
        if not search_term or not search_term.strip():
            return "Please provide a valid search term."

        search_term = search_term.strip().lower()

        # Get all users
        client = _get_iam_client()
        response = client.list_users()

        if isinstance(response, str):  # Error response
            return response

        users = response.get("Users", [])

        if not users:
            return "No IAM users found in your AWS account."

        # Filter users by search term
        matching_users = [
            user["UserName"]
            for user in users
            if search_term in user["UserName"].lower()
        ]

        if not matching_users:
            return f"No IAM users found matching '{search_term}'."

        return f"IAM users matching '{search_term}': {', '.join(matching_users)}."

    except Exception as e:
        logger.error(
            f"Error in search_iam_users with search term {search_term}", exc_info=e
        )
        return f"Failed to search IAM users: {str(e)}"
