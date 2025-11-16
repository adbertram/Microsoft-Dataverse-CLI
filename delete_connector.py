#!/usr/bin/env python3
"""
Script to delete a connector with dependency handling.
This uses the RetrieveDependenciesForDelete action to understand dependencies.
"""
import os
import sys
import json
from dotenv import load_dotenv
from dataverse_cli.client import get_client, ClientError

def retrieve_dependencies(client, connector_id):
    """Retrieve dependencies for a connector before deletion."""
    endpoint = "RetrieveDependenciesForDelete"

    data = {
        "ObjectId": connector_id,
        "ComponentType": 372  # Connector component type
    }

    try:
        result = client.post(endpoint, data)
        return result
    except ClientError as e:
        print(f"Error retrieving dependencies: {e}")
        return None

def delete_connector(connector_id, force=False):
    """Delete a connector by ID."""
    load_dotenv()

    try:
        client = get_client()

        # Get connector details first
        print(f"Fetching connector {connector_id}...")
        connector = client.get(f"connectors({connector_id})",
                              params={"$select": "connectorid,name,displayname"})
        print(f"Found connector: {connector.get('displayname')} ({connector.get('name')})")

        # Retrieve dependencies
        print("\nChecking for dependencies...")
        dependencies = retrieve_dependencies(client, connector_id)

        if dependencies:
            print(f"Dependencies found: {json.dumps(dependencies, indent=2)}")

        # Attempt deletion
        print(f"\nAttempting to delete connector {connector_id}...")
        client.delete(f"connectors({connector_id})")

        print(f"✓ Successfully deleted connector {connector_id}")
        return True

    except ClientError as e:
        print(f"✗ Failed to delete connector: {e}")

        # Check if it's a dependency error
        if "referenced by" in str(e).lower():
            print("\nThe connector has dependencies that must be removed first.")
            print("This may be an orphaned internal dependency.")
            print("\nOptions:")
            print("1. Remove the connector from the Power Automate portal")
            print("2. Use PowerShell with Remove-CrmRecord -Force")
            print("3. Contact support if the dependency is orphaned")

        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python delete_connector.py <connector_id>")
        sys.exit(1)

    connector_id = sys.argv[1]
    force = "--force" in sys.argv

    success = delete_connector(connector_id, force)
    sys.exit(0 if success else 1)
