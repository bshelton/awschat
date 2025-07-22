"""
AWS Assistant - Main Entry Point.
A user-friendly interface for the AWS Assistant agent.
"""

import sys
import os
import getpass

from logger import logger
from agent import agent


def print_banner() -> None:
    """Print the application banner."""
    print("\n" + "=" * 60)
    print("🤖 AWS Assistant - AI-Powered AWS Resource Manager")
    print("=" * 60)
    print("Type 'help' for available commands, 'exit' to quit")
    print("=" * 60 + "\n")


def print_help() -> None:
    """Print help information."""
    print("\n📚 AWS Assistant Help")
    print("-" * 40)
    print("Available commands:")
    print("• help - Show this help message")
    print("• status - Check AWS connection status")
    print("• commands - List available AWS operations")
    print("• clear - Clear conversation context")
    print("• context - Show conversation context summary")
    print("• exit/quit - Exit the application")
    print("\nExample queries:")
    print("• 'List all S3 buckets'")
    print("• 'Show me all IAM users'")
    print("• 'What's in my bucket named example-bucket?'")
    print("• 'Get details for IAM user john.doe'")
    print("• 'Find IAM users containing admin'")
    print("• 'Check for public S3 buckets'")
    print("\nYou can also ask natural language questions about your AWS resources!\n")


def print_status() -> None:
    """Print the current status of AWS connections."""
    print("\n🔍 Checking AWS Connection Status...")

    try:
        results = agent.test_aws_connection()

        print("\nAWS Service Status:")
        print("-" * 30)

        for service, status in results.items():
            status_icon = "✅" if status else "❌"
            status_text = "Connected" if status else "Failed"
            print(f"{status_icon} {service.upper()}: {status_text}")

        if not any(results.values()):
            print("\n⚠️  Warning: No AWS services are connected.")
            print("Please check your AWS credentials and permissions.")

        print()

    except Exception as e:
        print(f"❌ Error checking status: {e}")
        print()


def print_commands() -> None:
    """Print available AWS commands."""
    print("\n🛠️  Available AWS Operations:")
    print("-" * 40)

    try:
        commands = agent.get_available_commands()
        for command in commands:
            print(command)
        print()
    except Exception as e:
        print(f"❌ Error getting commands: {e}")
        print()


def setup_environment() -> bool:
    """Set up the environment with required credentials."""
    print("🔧 Setting up AWS Assistant...")

    if not os.environ.get("OPENAI_API_KEY"):
        print("\n🔑 OpenAI API Key Required")
        print("Please enter your OpenAI API key:")
        try:
            api_key = getpass.getpass("OpenAI API Key: ")
            if api_key.strip():
                os.environ["OPENAI_API_KEY"] = api_key
                print("✅ OpenAI API key set successfully")
            else:
                print("❌ OpenAI API key is required")
                return False
        except KeyboardInterrupt:
            print("\n❌ Setup cancelled")
            return False

    aws_configured = (
        os.environ.get("AWS_ACCESS_KEY_ID")
        or os.environ.get("AWS_PROFILE")
        or os.path.exists(os.path.expanduser("~/.aws/credentials"))
    )

    if not aws_configured:
        print("\n⚠️  AWS Credentials Not Found")
        print("Please configure your AWS credentials using one of these methods:")
        print(
            "1. Set environment variables: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
        )
        print("2. Use AWS CLI: aws configure")
        print("3. Set AWS_PROFILE environment variable")
        print("\nThe application will continue but AWS operations may fail.")

    return True


def main() -> None:
    """Main application loop."""
    try:
        print_banner()

        if not setup_environment():
            return

        try:
            print("🚀 Initializing AWS Assistant...")
            print("✅ AWS Assistant ready!")
        except Exception as e:
            print(f"❌ Failed to initialize AWS Assistant: {e}")
            print("Please check your configuration and try again.")
            return

        while True:
            try:
                query = input("\n🤖 Ask AWS Assistant: ").strip()

                if query.lower() in ["exit", "quit"]:
                    print("\n👋 Goodbye! Thanks for using AWS Assistant.")
                    break
                elif query.lower() == "help":
                    print_help()
                    continue
                elif query.lower() == "status":
                    print_status()
                    continue
                elif query.lower() == "commands":
                    print_commands()
                    continue
                elif query.lower() == "clear":
                    agent.clear_context()
                    print("🧹 Conversation history cleared.")
                    continue
                elif query.lower() == "context":
                    print(agent.get_context_summary())
                    continue
                elif not query:
                    print("Please enter a query or type 'help' for assistance.")
                    continue

                print("\n🔄 Processing your request...")
                response = agent.run(query)

                print(f"\n💬 Response:\n{response}")

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye! Thanks for using AWS Assistant.")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=e)
                print(f"\n❌ An error occurred: {e}")
                print("Please try again or type 'help' for assistance.")

    except Exception as e:
        logger.critical(f"Critical error in main: {e}", exc_info=e)
        print(f"\n💥 Critical error: {e}")
        print("Please check the logs for more details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
