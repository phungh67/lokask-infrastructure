# AWS Cross-Account Role Assumer

This Bash script automates the process of assuming an IAM role across different AWS accounts within an AWS Organization. By passing a text pattern, the script searches your organization for a matching account name, retrieves its Account ID, and attempts to assume the default OrganizationAccountAccessRole.

It outputs the necessary export commands to set your temporary AWS credentials in your active shell session and handles basic file-based logging for execution tracking.

## 📋 Prerequisites

Ensure the following tools are installed and configured on your host machine:

- AWS CLI: Authenticated with an identity that has permissions for organizations:ListAccounts and sts:AssumeRole.

- jq: A lightweight command-line JSON processor used to parse the AWS CLI output.

- Bash: Standard Unix shell environment.

## 🚀 Usage

Because the script generates export commands, you must execute it in a way that allows those variables to apply to your current shell environment. Using eval is the recommended approach.

```Bash
eval $(./script.sh <pattern> [session_prefix])
```

## Examples
1. Targeting a sandbox account with the default session name:

```Bash
eval $(./script.sh sandbox)
```
*(This assumes a role and sets the session name to something like terraform-15_10_2025)*

2. Targeting a production account with a custom session name:
```Bash
eval $(./script.sh prod deployment-pipeline)
```

## ⚙️ How It Works (Technical Flow)

1. **Account Discovery**: Executes `aws organizations list-accounts` and pipes the JSON output into `jq` to filter for the provided `<pattern>` (case-insensitive).

2. **Role Construction**: Injects the discovered Account ID into the standard role pattern: `arn:aws:iam::<account_id>:role/OrganizationAccountAccessRole`.

3. **STS Assume Role**: Calls `aws sts assume-role` using the generated ARN and a timestamped session name.

4. **Credential Injection**: Formats the resulting JSON credentials into standard bash `export` commands (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`) which are then evaluated by the parent shell.

## 📝 Logging

The script automatically generates execution logs in the directory where it is run, timestamped by the current date (e.g., `15_10_2025`).

- **Standard Execution Log**: `log-execution-<date>.log` - Records successful account matches and successful STS operations.

- **Error Log**: `log-execution-<date>.error` - Records failures, such as when no account matches the provided pattern.