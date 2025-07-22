# 🤖 AWS Assistant

An AI-powered assistant for AWS resource management that provides natural language interaction with your AWS infrastructure. Built with LangChain and OpenAI, this tool helps you explore and understand your AWS resources through conversational queries.

## ✨ Features

- **Natural Language Queries**: Ask questions about your AWS resources in plain English
- **Comprehensive AWS Support**: Currently supports S3, IAM and EC2 services
- **Retry Logic**: Automatic retry with exponential backoff for transient failures
- **User-Friendly Interface**: Interactive CLI with helpful commands and status checking

## 🚀 Quick Start

### Prerequisites

- Python 3.12 or higher
- AWS credentials configured
- OpenAI API key

### Installation

1. **Create a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure AWS credentials** (choose one method):

   **Option A: AWS CLI (Recommended)**

   ```bash
   aws configure
   ```

   **Option B: Environment variables**

   ```bash
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_DEFAULT_REGION=us-east-1
   ```

   **Option C: AWS credentials file**

   ```bash
   mkdir -p ~/.aws
   # Edit ~/.aws/credentials with your credentials
   ```

4. **Set up OpenAI API key**

   ```bash
   export OPENAI_API_KEY=your_openai_api_key
   ```

5. **Run the assistant**
   ```bash
   python main.py
   ```

## 📖 Usage

### Starting the Assistant

```bash
python main.py
```

The assistant will prompt you for your OpenAI API key if not already set in the environment.

### Available Commands

- `help` - Show help information and example queries
- `status` - Check AWS connection status for all services
- `commands` - List all available AWS operations
- `clear` - Clear conversation context/history
- `context` - Show conversation context summary
- `exit` or `quit` - Exit the application

### Example Queries

#### S3 Operations

```
"List all my S3 buckets"
"What's in my bucket named 'my-data-bucket'?"
"Show me all public S3 buckets"
"Get detailed information about bucket 'example-bucket'"
```

#### IAM Operations

```
"Show me all IAM users"
"List all IAM groups"
"What IAM policies do I have?"
"Get details for IAM user 'john.doe'"
"Find IAM users containing 'admin'"
```

#### EC2 Operations

```
"List all EC2 instances"
"Show me running instances only"
"What stopped instances do I have?"
"Get details for instance i-1234567890abcdef0"
"Find instances with 'web' in the name"
```

#### Natural Language Queries

```
"Who has access to my AWS account?"
"What resources are publicly accessible?"
"Show me a summary of my AWS setup"
"Are there any security concerns I should know about?"
```

## ⚙️ Configuration

The application uses `config.yaml` for configuration. Key settings include:

```yaml
# OpenAI Configuration
openai:
  model: "gpt-4o-mini"
  provider: "openai"
  max_tokens: 1000
  temperature: 0.1

# AWS Configuration
aws:
  region: "us-east-1"
  max_retries: 3
  timeout: 30

# Logging Configuration
logging:
  level: "INFO"
  file: "aws_assistant.log"
  max_size: "10MB"
  backup_count: 5

# Available AWS Services
services:
  s3: true
  iam: true
  ec2: false # Future expansion
```

## 🛠️ Available Tools

### S3 Tools

- `list_s3_buckets` - List all S3 buckets
- `list_public_s3_buckets` - Find publicly accessible buckets
- `inspect_s3_bucket` - List contents of a specific bucket
- `get_s3_bucket_info` - Get detailed bucket information

### IAM Tools

- `list_iam_users` - List all IAM users
- `list_iam_groups` - List all IAM groups
- `list_iam_policies` - List all IAM policies
- `list_iam_roles` - List all IAM roles
- `get_iam_user_details` - Get detailed user information
- `search_iam_users` - Search for users by name

### EC2 Tools

- `list_ec2_instances` - List all EC2 instances with key information
- `get_ec2_instance_details` - Get detailed information about a specific instance
- `list_running_ec2_instances` - List only running instances
- `search_ec2_instances` - Search for instances by name or ID

## 📝 Logging

The application provides comprehensive logging:

- **Console Output**: Real-time status and error messages
- **File Logging**: Rotating log files with configurable size limits
- **Structured Logging**: JSON-formatted logs for easy parsing
- **Error Tracking**: Detailed error context and stack traces

Log files are stored in `aws_assistant.log` by default.

## 🔧 Troubleshooting

### Common Issues

**1. AWS Credentials Not Found**

```
Error: AWS credentials not found. Please configure your AWS credentials.
```

**Solution**: Configure AWS credentials using one of the methods in the installation section.

**2. OpenAI API Key Required**

```
Error: Missing required environment variables: OPENAI_API_KEY
```

**Solution**: Set your OpenAI API key as an environment variable or enter it when prompted.

**3. Access Denied Errors**

```
Error: Access denied to s3. Please check your permissions.
```

**Solution**: Ensure your AWS credentials have the necessary permissions for the services you're trying to access.

**4. Rate Limiting**

```
Error: AWS API rate limit exceeded. Please try again later.
```

**Solution**: The application automatically retries with exponential backoff. Wait a moment and try again.

### Debug Mode

To enable debug logging, modify `config.yaml`:

```yaml
logging:
  level: "DEBUG"
```

### Checking Connection Status

Use the `status` command to verify AWS connectivity:

```bash
🤖 Ask AWS Assistant: status
```

## 🔒 Security Considerations

- **Read-Only Access**: The assistant only performs read operations on AWS resources
- **No Credential Storage**: Credentials are not stored by the application
- **Secure Logging**: Sensitive information is not logged
- **Permission Requirements**: Minimal IAM permissions required

### Required IAM Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListAllMyBuckets",
        "s3:GetBucketAcl",
        "s3:ListBucket",
        "iam:ListUsers",
        "iam:ListGroups",
        "iam:ListPolicies",
        "iam:ListRoles",
        "iam:GetUser",
        "iam:ListGroupsForUser",
        "iam:ListUserPolicies",
        "iam:ListAttachedUserPolicies"
      ],
      "Resource": "*"
    }
  ]
}
```

## 🏗️ Architecture

```
aws-assistant/
├── main.py              # Main entry point
├── agent.py             # Core agent implementation
├── config_manager.py    # Configuration management
├── logger.py            # Logging system
├── aws_client.py        # AWS client with error handling
├── config.yaml          # Configuration file
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── tools/
    └── aws/
        ├── s3.py       # S3 tools
        └── iam.py      # IAM tools
        └── ec2.py      # EC2 tools
```
