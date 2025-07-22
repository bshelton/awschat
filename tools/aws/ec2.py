"""
EC2 tools for AWS Assistant.
Provides tools for EC2 operations with formatted responses.
"""

from datetime import datetime
from langchain_core.tools import tool
from aws_client import AWSClient
from logger import logger


class EC2Client(AWSClient):
    """EC2 client with specialized operations."""

    def __init__(self, region: str = None):
        super().__init__("ec2", region)

    def describe_instances(self, **kwargs):
        """Describe EC2 instances."""
        return self.execute_with_retry(
            "describe_instances", self.client.describe_instances, **kwargs
        )

    def describe_instance(self, instance_id: str):
        """Describe a specific EC2 instance."""
        return self.execute_with_retry(
            "describe_instances",
            self.client.describe_instances,
            InstanceIds=[instance_id],
        )

    def describe_security_groups(self, **kwargs):
        """Describe security groups."""
        return self.execute_with_retry(
            "describe_security_groups", self.client.describe_security_groups, **kwargs
        )


# Global EC2 client instance - will be initialized when needed
ec2_client = None


def _get_ec2_client():
    """Get or create EC2 client instance."""
    global ec2_client
    if ec2_client is None:
        ec2_client = EC2Client()
    return ec2_client


def _format_instance_info(instance):
    """Format instance information for display."""
    instance_id = instance.get("InstanceId", "Unknown")
    state = instance.get("State", {}).get("Name", "Unknown")
    instance_type = instance.get("InstanceType", "Unknown")
    launch_time = instance.get("LaunchTime")
    private_ip = instance.get("PrivateIpAddress", "N/A")

    # Get instance name from tags
    name = "Unnamed"
    if "Tags" in instance:
        for tag in instance["Tags"]:
            if tag.get("Key") == "Name":
                name = tag.get("Value", "Unnamed")
                break

    # Format launch time
    if isinstance(launch_time, datetime):
        launch_time_str = launch_time.strftime("%Y-%m-%d %H:%M:%S UTC")
    else:
        launch_time_str = str(launch_time) if launch_time else "Unknown"

    return {
        "id": instance_id,
        "name": name,
        "state": state,
        "type": instance_type,
        "launch_time": launch_time_str,
        "private_ip": private_ip,
    }


@tool
def list_ec2_instances() -> str:
    """
    Returns a formatted list of all EC2 instances with key information.
    """
    try:
        logger.info("Executing list_ec2_instances tool")
        client = _get_ec2_client()
        response = client.describe_instances()

        if isinstance(response, str):  # Error response
            return response

        instances = []
        for reservation in response.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                instance_info = _format_instance_info(instance)
                instances.append(
                    f"{instance_info['id']} ({instance_info['name']}) - "
                    f"{instance_info['type']} - {instance_info['state']} - "
                    f"Launched: {instance_info['launch_time']}"
                )

        if not instances:
            return "No EC2 instances found in your AWS account."

        return f"EC2 instances: {'; '.join(instances)}."

    except Exception as e:
        logger.error("Error in list_ec2_instances", exc_info=e)
        return f"Failed to list EC2 instances: {str(e)}"


@tool
def get_ec2_instance_details(instance_id: str) -> str:
    """
    Gets detailed information about a specific EC2 instance.

    Args:
        instance_id: The ID of the EC2 instance (e.g., i-1234567890abcdef0)
    """
    try:
        logger.info(
            f"Executing get_ec2_instance_details tool for instance: {instance_id}"
        )

        if not instance_id or not instance_id.strip():
            return "Please provide a valid instance ID."

        instance_id = instance_id.strip()
        client = _get_ec2_client()
        response = client.describe_instance(instance_id)

        if isinstance(response, str):  # Error response
            return response

        instances = response.get("Reservations", [{}])[0].get("Instances", [])

        if not instances:
            return f"Instance {instance_id} not found."

        instance = instances[0]
        instance_info = _format_instance_info(instance)

        # Get additional details
        security_groups = [
            sg.get("GroupName", sg.get("GroupId", "Unknown"))
            for sg in instance.get("SecurityGroups", [])
        ]
        vpc_id = instance.get("VpcId", "N/A")
        subnet_id = instance.get("SubnetId", "N/A")
        availability_zone = instance.get("Placement", {}).get("AvailabilityZone", "N/A")

        result = [
            f"Instance {instance_info['id']} details:",
            f"- Name: {instance_info['name']}",
            f"- State: {instance_info['state']}",
            f"- Type: {instance_info['type']}",
            f"- Launch Time: {instance_info['launch_time']}",
            f"- Private IP: {instance_info['private_ip']}",
            f"- VPC: {vpc_id}",
            f"- Subnet: {subnet_id}",
            f"- Availability Zone: {availability_zone}",
            f"- Security Groups: {', '.join(security_groups) if security_groups else 'None'}",
        ]

        return "\n".join(result)

    except Exception as e:
        logger.error(
            f"Error in get_ec2_instance_details for instance {instance_id}", exc_info=e
        )
        return f"Failed to get details for instance {instance_id}: {str(e)}"


@tool
def list_running_ec2_instances() -> str:
    """
    Returns a list of only running EC2 instances.
    """
    try:
        logger.info("Executing list_running_ec2_instances tool")
        client = _get_ec2_client()
        response = client.describe_instances(
            Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
        )

        if isinstance(response, str):  # Error response
            return response

        instances = []
        for reservation in response.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                instance_info = _format_instance_info(instance)
                instances.append(
                    f"{instance_info['id']} ({instance_info['name']}) - "
                    f"{instance_info['type']} - {instance_info['private_ip']}"
                )

        if not instances:
            return "No running EC2 instances found."

        return f"Running EC2 instances: {'; '.join(instances)}."

    except Exception as e:
        logger.error("Error in list_running_ec2_instances", exc_info=e)
        return f"Failed to list running EC2 instances: {str(e)}"


@tool
def search_ec2_instances(search_term: str) -> str:
    """
    Searches for EC2 instances by name or ID.

    Args:
        search_term: The search term to match against instance names or IDs
    """
    try:
        logger.info(
            f"Executing search_ec2_instances tool with search term: {search_term}"
        )

        if not search_term or not search_term.strip():
            return "Please provide a valid search term."

        search_term = search_term.strip().lower()
        client = _get_ec2_client()
        response = client.describe_instances()

        if isinstance(response, str):  # Error response
            return response

        matching_instances = []
        for reservation in response.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                instance_id = instance.get("InstanceId", "").lower()

                # Check instance name from tags
                instance_name = ""
                if "Tags" in instance:
                    for tag in instance["Tags"]:
                        if tag.get("Key") == "Name":
                            instance_name = tag.get("Value", "").lower()
                            break

                # Check if search term matches
                if search_term in instance_id or search_term in instance_name:
                    instance_info = _format_instance_info(instance)
                    matching_instances.append(
                        f"{instance_info['id']} ({instance_info['name']}) - "
                        f"{instance_info['type']} - {instance_info['state']}"
                    )

        if not matching_instances:
            return f"No EC2 instances found matching '{search_term}'."

        return (
            f"EC2 instances matching '{search_term}': {'; '.join(matching_instances)}."
        )

    except Exception as e:
        logger.error(
            f"Error in search_ec2_instances with search term {search_term}", exc_info=e
        )
        return f"Failed to search EC2 instances: {str(e)}"
