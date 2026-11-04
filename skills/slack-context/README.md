# Slack Context Skill

Extract context from Slack conversations to inform agent tasks and decisions.

## Security

This skill accesses Slack messages which may contain:
- Personal information (PII)
- Confidential business information
- Private conversations
- Credentials or secrets
- Internal-only discussions

The skill uses fetched content without a separate review or confirmation step. It must omit
credentials, tokens, customer data, and unrelated personal details from outputs.

## Prerequisites

### 1. Install gh slack extension

```bash
gh extension install rneatherway/gh-slack
```

### 2. Configure authentication

```bash
# Set up Slack authentication for your team
eval $(gh slack auth -t github)
```

### 3. Verify access

```bash
# Test reading a public message
gh slack read <slack-permalink>
```

## When to Use This Skill

**Good use cases:**
- Technical discussions about implementation approaches
- Public feature requests or bug reports
- Architecture decisions documented in Slack
- Team discussions about code structure
- Open-source project planning

**Bad use cases:**
- Private customer conversations
- HR or personnel discussions
- Security incident details
- Confidential product plans
- Anything with PII or credentials

## Installation

### Personal Skills
```bash
cp -r slack-context ~/.copilot/skills/
```

### Project Skills
```bash
cp -r slack-context /path/to/repo/.github/skills/
```

## Usage

This skill activates when you ask Copilot to:
- "Fetch context from this Slack thread: [link]"
- "Read this Slack conversation and help me implement what we discussed"
- "Get the requirements from this Slack thread"
- "Extract the technical details from this chat"

The skill will:
1. Fetch the Slack thread using `gh slack read`
2. Remove sensitive or unrelated details from its output
3. Use the context for your task without another confirmation

## Features

- **No confirmation pause** - Uses fetched context right away
- **Thread extraction** - Pulls full conversation threads, not just single messages
- **Context formatting** - Structures Slack messages for agent consumption
- **Safe output** - Omits secrets and unrelated sensitive details

## Examples

### Extract feature requirements
```bash
# User: "Fetch the requirements from this Slack thread: https://github.slack.com/archives/C123/p456"
# Agent: Fetched the thread and found a discussion about adding OAuth support.
#        [Continues with the requested task.]
```

### Implementation guidance
```bash
# User: "Read this conversation and help implement what we discussed"
# Agent: Fetched 5 messages discussing API rate limiting.
#        Key points:
#        - Use token bucket algorithm
#        - 100 requests per minute limit
#        - Return 429 with Retry-After header
#        [Continues with implementation.]
```

## Best Practices

1. **Omit sensitive info** like credentials, tokens, and customer data
2. **Keep only needed context** for the task
3. **Use public channels** when possible
4. **Link to issues/PRs** instead when appropriate (they're safer)
5. **Delete context** after task completion if it's sensitive

---

**Required:** GitHub CLI with [`gh-slack`](https://github.com/rneatherway/gh-slack) extension installed and configured
