Here's your rewritten GitHub README file:

# CEB-Outage-Checker

A tool that checks for Ceylon Electricity Board (CEB) outages affecting your registered accounts and sends notifications.

## Setup Instructions

### 1. Repository Configuration

1. Go to your repository on GitHub
2. Navigate to **Settings** > **Secrets and variables** > **Actions**
3. Add the following secrets:
   - `CEB_USERNAME` - Your CEB portal username
   - `CEB_PASSWORD` - Your CEB portal password
   - `NTFY_URL` - Your notification URL (e.g., `https://ntfy.sh/your-topic`)
   - `CEB_ACCOUNTS` - JSON array of your CEB accounts in the format:
     ```json
     [
       {"AcctNo":"1111111111","AcctName":"Location 1"},
       {"AcctNo":"2222222222","AcctName":"Location 2"}
     ]
     ```

### 2. Workflow Permissions

1. Go to **Settings** > **Actions** > **General**
2. Under **Workflow permissions**, select **Read and write permissions**

## Usage

Once configured, the tool will automatically check for outages affecting your registered accounts and send notifications to your specified NTFY topic.
