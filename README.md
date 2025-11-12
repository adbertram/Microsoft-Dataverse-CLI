# Dataverse CLI

A powerful Python CLI and library for Microsoft Dataverse and Power Automate. Manage flows, solutions, entities, and more from the command line or in your Python applications.

## Features

- ✅ **Power Automate Flow Management** - Create, list, update, delete, and manage flows
- ✅ **Solution Operations** - Query solutions and their components
- ✅ **Entity/Table Queries** - Query any Dataverse entity with OData filters
- ✅ **Multiple Authentication Methods** - Service principal, user credentials, or access token
- ✅ **Rich CLI Output** - JSON and table formats with syntax highlighting
- ✅ **Python Library** - Use as a library in your Python applications
- ✅ **Type Hints** - Full type hints for better IDE support

## Installation

### Using pipx (Recommended)

```bash
cd ~/Dropbox/GitRepos/Microsoft-Dataverse-CLI
pipx install -e .
```

This installs the CLI globally and makes the `dataverse` command available without activating a virtual environment.

If pipx is not installed:
```bash
brew install pipx
pipx ensurepath
```

### From Source (Development with venv)

```bash
cd ~/Dropbox/GitRepos/Microsoft-Dataverse-CLI
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

### From PyPI (When Published)

```bash
pipx install dataverse-cli
```

## Configuration

Copy the example configuration file and fill in your credentials:

```bash
cp .env.example .env
```

Then edit `.env` with your actual values:

### Service Principal Authentication (Recommended for CLI)

```bash
DATAVERSE_URL=https://your-org.crm.dynamics.com
DATAVERSE_CLIENT_ID=your-azure-app-client-id
DATAVERSE_CLIENT_SECRET=your-azure-app-client-secret
DATAVERSE_TENANT_ID=your-azure-tenant-id
```

### User Authentication

```bash
DATAVERSE_URL=https://your-org.crm.dynamics.com
DATAVERSE_CLIENT_ID=your-azure-app-client-id
DATAVERSE_TENANT_ID=your-azure-tenant-id
DATAVERSE_USERNAME=your-username
DATAVERSE_PASSWORD=your-password
```

### Access Token Authentication

```bash
DATAVERSE_URL=https://your-org.crm.dynamics.com
DATAVERSE_ACCESS_TOKEN=your-access-token
```

## Quick Start

### Verify Authentication

```bash
dataverse auth test
dataverse auth whoami
```

### List Power Automate Flows

```bash
# List all flows
dataverse flow list

# List flows in table format
dataverse flow list --table

# Filter by solution
dataverse flow list --solution "Progress Content Automation"

# Filter by state
dataverse flow list --state activated
```

### Create a New Flow

```bash
# Create a flow with HTTP trigger
dataverse flow create --name "My Flow" --trigger http

# Create a flow in a specific solution
dataverse flow create --name "My Flow" --trigger http --solution-id <solution-guid>
```

### Manage Flows

```bash
# Get flow details
dataverse flow get <flow-id>

# Update flow name
dataverse flow update <flow-id> --name "New Name"

# Activate a flow
dataverse flow activate <flow-id>

# Deactivate a flow
dataverse flow deactivate <flow-id>

# Delete a flow
dataverse flow delete <flow-id> --yes
```

### Solution Operations

```bash
# List all solutions
dataverse solution list
dataverse solution list --table

# Get solution by name
dataverse solution get --name "Progress Content Automation"

# List flows in a solution
dataverse solution flows --name "Progress Content Automation" --table
```

### Entity Queries

```bash
# Query any entity with OData filters
dataverse entity query workflows --filter "category eq 5" --top 10

# Get specific record
dataverse entity get workflows <workflow-id>

# Count records
dataverse entity count workflows --filter "category eq 5"

# Get entity metadata
dataverse entity metadata workflow
```

## Command Reference

### Flow Commands

| Command | Description |
|---------|-------------|
| `flow list` | List all Power Automate flows |
| `flow get <id>` | Get flow details |
| `flow create` | Create a new flow |
| `flow update <id>` | Update flow properties |
| `flow delete <id>` | Delete a flow |
| `flow activate <id>` | Turn on a flow |
| `flow deactivate <id>` | Turn off a flow |

### Solution Commands

| Command | Description |
|---------|-------------|
| `solution list` | List all solutions |
| `solution get` | Get solution details |
| `solution flows` | List flows in a solution |
| `solution components` | List solution components |

### Entity Commands

| Command | Description |
|---------|-------------|
| `entity query <entity>` | Query entity records |
| `entity get <entity> <id>` | Get specific record |
| `entity count <entity>` | Count records |
| `entity metadata <entity>` | Get entity metadata |

### Auth Commands

| Command | Description |
|---------|-------------|
| `auth test` | Test authentication |
| `auth token` | Get access token |
| `auth whoami` | Display current user info |

## Using as a Python Library

```python
from dataverse_cli.client import get_client

# Get authenticated client
client = get_client()

# Query flows
result = client.get("workflows", params={"$filter": "category eq 5"})
flows = result.get("value", [])

# Create a flow
flow_data = {
    "name": "My Flow",
    "category": 5,
    "type": 1,
    # ... other properties
}
result = client.post("workflows", data=flow_data)

# Update a flow
client.patch(f"workflows({flow_id})", data={"name": "Updated Name"})

# Delete a flow
client.delete(f"workflows({flow_id})")
```

## Development

### Setup Development Environment

```bash
# Navigate to repository
cd ~/Dropbox/GitRepos/Microsoft-Dataverse-CLI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
pytest --cov=dataverse_cli --cov-report=html
```

### Code Formatting

```bash
black dataverse_cli/
```

## Azure App Registration Setup

To use service principal authentication, you need an Azure AD app registration:

1. **Create App Registration** in Azure Portal
2. **Add API Permission**: Dynamics CRM `user_impersonation`
3. **Create Client Secret** in Certificates & secrets
4. **Add Service Principal to Dataverse**:
   - Go to Power Platform Admin Center
   - Navigate to your environment → Settings → Users + permissions → Application users
   - Add app user with your Client ID
   - Assign appropriate security role (e.g., System Administrator)

## Project Structure

```
Microsoft-Dataverse-CLI/
├── dataverse_cli/
│   ├── __init__.py           # Package initialization
│   ├── client.py             # API client and authentication
│   ├── config.py             # Configuration management
│   ├── main.py               # CLI entry point
│   ├── output.py             # Output formatting utilities
│   └── commands/
│       ├── __init__.py
│       ├── flow.py           # Flow commands
│       ├── solution.py       # Solution commands
│       ├── auth.py           # Auth commands
│       └── entity.py         # Entity query commands
├── tests/                    # Test suite
├── pyproject.toml            # Project configuration
├── README.md                 # This file
└── .env.example              # Example configuration
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.

## Resources

- [Dataverse Web API Documentation](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/webapi/overview)
- [Power Automate Documentation](https://learn.microsoft.com/en-us/power-automate/)
- [MSAL Python Documentation](https://msal-python.readthedocs.io/)
- [Typer Documentation](https://typer.tiangolo.com/)

## Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/adbertram/dataverse-cli).
