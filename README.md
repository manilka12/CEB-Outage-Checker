CEB-Outage-Checker
A tool that checks for Ceylon Electricity Board (CEB) outages affecting your registered accounts and sends notifications.
Setup Instructions
1. Repository Configuration

Go to your repository on GitHub
Navigate to Settings > Secrets and variables > Actions
Add the following secrets:

CEB_USERNAME - Your CEB portal username
CEB_PASSWORD - Your CEB portal password
NTFY_URL - Your notification URL (e.g., https://ntfy.sh/your-topic)
CEB_ACCOUNTS - JSON array of your CEB accounts in the format:
jsonCopy[
  {"AcctNo":"1111111111","AcctName":"Location 1"},
  {"AcctNo":"2222222222","AcctName":"Location 2"}
]




2. Workflow Permissions

Go to Settings > Actions > General
Under Workflow permissions, select Read and write permissions

Usage
Once configured, the tool will automatically check for outages affecting your registered accounts and send notifications to your specified NTFY topic.
