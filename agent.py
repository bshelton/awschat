"""
AWS Assistant Agent.
Main agent module that orchestrates AWS operations with AI assistance.
"""

from typing import List, Dict
from langchain.chat_models import init_chat_model
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from config_manager import config
from logger import logger

# Import tools based on configuration
from tools.aws.s3 import (
    list_s3_buckets,
    list_public_s3_buckets,
    inspect_s3_bucket,
    get_s3_bucket_info,
)
from tools.aws.iam import (
    list_iam_users,
    list_iam_groups,
    list_iam_policies,
    list_iam_roles,
    get_iam_user_details,
    search_iam_users,
)
from tools.aws.ec2 import (
    list_ec2_instances,
    get_ec2_instance_details,
    list_running_ec2_instances,
    search_ec2_instances,
)


class AWSAssistantAgent:
    """Main AWS Assistant agent with comprehensive error handling and logging."""

    def __init__(self):
        """Initialize the AWS Assistant agent."""
        self.logger = logger
        self._validate_environment()
        self._setup_model()
        self._setup_tools()
        self._setup_agent()
        self.chat_history = []
        self.logger.info("AWS Assistant agent initialized successfully")

    def _validate_environment(self) -> None:
        """Validate required environment variables and AWS credentials."""
        try:
            config.validate_environment()
            self.logger.info("Environment validation passed")
        except ValueError as e:
            self.logger.critical(f"Environment validation failed: {e}")
            raise

    def _setup_model(self) -> None:
        """Set up the OpenAI model with configuration."""
        try:
            openai_config = config.get_openai_config()
            self.model = init_chat_model(
                openai_config.get("model", "gpt-4o-mini"),
                model_provider=openai_config.get("provider", "openai"),
            )
            self.logger.info(
                f"OpenAI model initialized: {openai_config.get('model', 'gpt-4o-mini')}"
            )
        except Exception as e:
            self.logger.critical(f"Failed to initialize OpenAI model: {e}", exc_info=e)
            raise

    def _setup_tools(self) -> None:
        """Set up available tools based on configuration."""
        self.tools = []

        if config.is_service_enabled("s3"):
            self.tools.extend(
                [
                    list_s3_buckets,
                    list_public_s3_buckets,
                    inspect_s3_bucket,
                    get_s3_bucket_info,
                ]
            )
            self.logger.info("S3 tools enabled")

        if config.is_service_enabled("iam"):
            self.tools.extend(
                [
                    list_iam_users,
                    list_iam_groups,
                    list_iam_policies,
                    list_iam_roles,
                    get_iam_user_details,
                    search_iam_users,
                ]
            )
            self.logger.info("IAM tools enabled")

        if config.is_service_enabled("ec2"):
            self.tools.extend(
                [
                    list_ec2_instances,
                    get_ec2_instance_details,
                    list_running_ec2_instances,
                    search_ec2_instances,
                ]
            )
            self.logger.info("EC2 tools enabled")

        if not self.tools:
            self.logger.warning("No AWS service tools are enabled")
        else:
            self.logger.info(f"Loaded {len(self.tools)} tools")

    def _setup_agent(self) -> None:
        """Set up the LangChain agent with tools and prompt."""
        try:
            agent_config = config.get_agent_config()

            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "You are AWS Assistant, an AI-powered tool created by Brock Shelton to help users interact with AWS services in a read-only capacity. "
                        "Your capabilities include providing detailed information about AWS resources, such as S3 buckets, IAM users, groups, policies, roles, and EC2 instances. "
                        "You have strictly read-only access; you cannot create, modify, or delete any resources. "
                        "Always respond clearly and helpfully, explaining each action or command you describe. "
                        "For every tool output or information provided, include concise commentary and use clear formatting for readability, such as line breaks or bullet points. "
                        "If you encounter errors or limitations, explain them in friendly, non-technical language. "
                        "If a request is outside your read-only scope or unclear, politely inform the user and suggest what information you can provide. "
                        "You were created by Brock Shelton. ",
                    ),
                    MessagesPlaceholder(variable_name="chat_history"),
                    ("human", "{input}"),
                    MessagesPlaceholder(variable_name="agent_scratchpad"),
                ]
            )

            self.agent = create_openai_functions_agent(self.model, self.tools, prompt)

            self.executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                verbose=agent_config.get("verbose", True),
                max_iterations=agent_config.get("max_iterations", 10),
                return_intermediate_steps=agent_config.get(
                    "return_intermediate_steps", False
                ),
                handle_parsing_errors=True,
            )

            self.logger.info("Agent executor created successfully")

        except Exception as e:
            self.logger.critical(f"Failed to set up agent: {e}", exc_info=e)
            raise

    def run(self, query: str) -> str:
        """
        Run the agent with a user query.

        Args:
            query: The user's query or command

        Returns:
            The agent's response
        """
        if not query or not query.strip():
            return "Please provide a valid query."

        query = query.strip()
        self.logger.debug(f"Processing query: {query}")

        try:
            result = self.executor.invoke(
                {"input": query, "chat_history": self.chat_history}
            )
            response = result.get("output", "No response generated.")
            response = self._fix_response_spacing(response)
            self.logger.debug("Query processed successfully")

            # Update chat history with this exchange
            self.chat_history.extend([("human", query), ("ai", response)])

            return response

        except Exception as e:
            error_msg = f"Failed to process query: {str(e)}"
            self.logger.error(error_msg, exc_info=e)
            return f"I encountered an error while processing your request: {str(e)}"

    def _fix_response_spacing(self, response: str) -> str:
        """Fix spacing issues in the response."""
        import re

        # Add space after periods followed by capital letters
        response = re.sub(r"\.([A-Z])", r". \1", response)
        # Add space after periods followed by numbers
        response = re.sub(r"\.(\d)", r". \1", response)
        return response

    def get_available_commands(self) -> List[str]:
        """Get a list of available commands and their descriptions."""
        commands = []

        for tool in self.tools:
            name = tool.name
            description = tool.description or "No description available"

            if name.startswith("list_"):
                category = name.split("_")[1].upper()
                commands.append(f"• {name}: List all {category} resources")
            elif name.startswith("get_"):
                commands.append(
                    f"• {name}: Get detailed information about a specific resource"
                )
            elif name.startswith("search_"):
                commands.append(f"• {name}: Search for resources matching a term")
            elif name.startswith("inspect_"):
                commands.append(f"• {name}: Inspect the contents of a resource")
            else:
                commands.append(f"• {name}: {description}")

        return commands

    def test_aws_connection(self) -> Dict[str, bool]:
        """Test connections to AWS services."""
        results = {}

        if config.is_service_enabled("s3"):
            try:
                from aws_client import AWSClient

                s3_client = AWSClient("s3")
                results["s3"] = s3_client.test_connection()
            except Exception as e:
                self.logger.error("S3 connection test failed", exc_info=e)
                results["s3"] = False

        if config.is_service_enabled("iam"):
            try:
                from aws_client import AWSClient

                iam_client = AWSClient("iam")
                results["iam"] = iam_client.test_connection()
            except Exception as e:
                self.logger.error("IAM connection test failed", exc_info=e)
                results["iam"] = False

        return results

    def clear_context(self):
        """Clear the conversation history."""
        self.chat_history = []

    def get_context_summary(self):
        """Get a summary of the current conversation context."""
        return f"Conversation has {len(self.chat_history)} exchanges"


# Global agent instance - will be initialized when needed
_agent_instance = None


def get_agent():
    """Get or create the global agent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = AWSAssistantAgent()
    return _agent_instance


class LazyAgent:
    def __getattr__(self, name):
        return getattr(get_agent(), name)


agent = LazyAgent()
