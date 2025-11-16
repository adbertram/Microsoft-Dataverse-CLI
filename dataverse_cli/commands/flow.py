"""Dataverse workflow commands for Dataverse CLI."""
import json
import typer
from typing import Optional
from pathlib import Path

from ..client import get_client
from ..output import (
    print_json,
    print_table,
    print_success,
    print_error,
    handle_api_error,
    format_response,
)

app = typer.Typer(help="Manage Dataverse workflows")


@app.command("list")
def list_flows(
    solution: Optional[str] = typer.Option(None, "--solution", "-s", help="Filter by solution name"),
    state: Optional[str] = typer.Option(None, "--state", help="Filter by state: draft, activated"),
    table_format: bool = typer.Option(False, "--table", "-t", help="Display as table"),
):
    """
    List all Dataverse workflows.

    Examples:
        dataverse flow list
        dataverse flow list --solution "Progress Content Automation"
        dataverse flow list --state activated --table
    """
    try:
        client = get_client()

        # Build OData filter
        filters = ["category eq 5"]  # Modern cloud flows

        if state:
            state_code = 1 if state.lower() == "activated" else 0
            filters.append(f"statecode eq {state_code}")

        filter_query = " and ".join(filters)
        params = {
            "$filter": filter_query,
            "$select": "workflowid,name,statecode,statuscode,createdon,modifiedon,solutionid",
            "$orderby": "modifiedon desc"
        }

        result = client.get("workflows", params=params)
        flows = format_response(result)

        # Filter by solution if specified
        if solution and isinstance(flows, list):
            # Get solution ID
            solution_params = {"$filter": f"friendlyname eq '{solution}'", "$select": "solutionid"}
            solution_result = client.get("solutions", params=solution_params)
            solutions = format_response(solution_result)

            if solutions:
                solution_id = solutions[0].get("solutionid")
                flows = [f for f in flows if f.get("solutionid") == solution_id]

        if table_format and isinstance(flows, list):
            # Format state for display
            for flow in flows:
                flow["state"] = "Activated" if flow.get("statecode") == 1 else "Draft"

            print_table(flows, ["name", "workflowid", "state", "modifiedon"])
        else:
            print_json(flows)

    except Exception as e:
        exit_code = handle_api_error(e)
        raise typer.Exit(exit_code)


@app.command("get")
def get_flow(
    flow_id: str = typer.Argument(..., help="Flow ID (GUID)"),
):
    """
    Get detailed information about a specific flow.

    Examples:
        dataverse flow get 29e2253b-cabc-f011-bbd3-000d3a8ba54e
    """
    try:
        client = get_client()
        result = client.get(f"workflows({flow_id})")
        formatted = format_response(result)
        print_json(formatted)

    except Exception as e:
        exit_code = handle_api_error(e)
        raise typer.Exit(exit_code)


@app.command("create")
def create_flow(
    name: str = typer.Option(..., "--name", "-n", help="Flow name"),
    trigger: str = typer.Option("http", "--trigger", help="Trigger type: http, manual, scheduled"),
    solution_id: Optional[str] = typer.Option(None, "--solution-id", help="Solution ID to add flow to"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="Flow description"),
):
    """
    Create a new Dataverse workflow.

    Examples:
        dataverse flow create --name "My Flow" --trigger http
        dataverse flow create --name "My Flow" --trigger http --solution-id <guid>
    """
    try:
        client = get_client()

        # Build flow definition based on trigger type
        if trigger.lower() == "http":
            trigger_def = {
                "Incoming_Topics": {
                    "type": "Request",
                    "kind": "Http",
                    "inputs": {
                        "schema": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                }
            }
        elif trigger.lower() == "manual":
            trigger_def = {
                "manual": {
                    "type": "Request",
                    "kind": "Button",
                    "inputs": {
                        "schema": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                }
            }
        else:
            print_error(f"Unsupported trigger type: {trigger}")
            raise typer.Exit(1)

        clientdata = {
            "properties": {
                "connectionReferences": {},
                "definition": {
                    "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
                    "contentVersion": "1.0.0.0",
                    "parameters": {
                        "$authentication": {
                            "defaultValue": {},
                            "type": "SecureObject"
                        },
                        "$connections": {
                            "defaultValue": {},
                            "type": "Object"
                        }
                    },
                    "triggers": trigger_def,
                    "actions": {}
                }
            },
            "schemaVersion": "1.0.0.0"
        }

        # Build workflow record
        data = {
            "name": name,
            "type": 1,
            "category": 5,
            "primaryentity": "none",
            "mode": 0,
            "ondemand": False,
            "subprocess": False,
            "scope": 4,
            "triggeroncreate": False,
            "triggerondelete": False,
            "asyncautodelete": False,
            "syncworkflowlogonfailure": False,
            "statecode": 0,
            "statuscode": 1,
            "clientdata": json.dumps(clientdata),
            "istransacted": True,
            "runas": 1,
            "modernflowtype": 0,
            "clientdataiscompressed": False
        }

        if description:
            data["description"] = description

        if solution_id:
            data["solutionid"] = solution_id

        result = client.post("workflows", data)
        flow_id = result.get("workflowid") or result.get("id")

        print_success(f"Flow created successfully: {flow_id}")
        print_json({"flow_id": flow_id, "name": name, "trigger": trigger})

    except Exception as e:
        exit_code = handle_api_error(e)
        raise typer.Exit(exit_code)


@app.command("update")
def update_flow(
    flow_id: str = typer.Argument(..., help="Flow ID (GUID)"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="New flow name"),
    description: Optional[str] = typer.Option(None, "--description", "-d", help="New description"),
    state: Optional[str] = typer.Option(None, "--state", help="State: draft, activated"),
):
    """
    Update an existing Dataverse workflow.

    Examples:
        dataverse flow update <flow-id> --name "New Name"
        dataverse flow update <flow-id> --state activated
        dataverse flow update <flow-id> --description "New description"
    """
    try:
        client = get_client()

        data = {}
        if name:
            data["name"] = name
        if description:
            data["description"] = description
        if state:
            data["statecode"] = 1 if state.lower() == "activated" else 0

        if not data:
            print_error("No update parameters provided")
            raise typer.Exit(1)

        client.patch(f"workflows({flow_id})", data)
        print_success(f"Flow updated successfully: {flow_id}")

    except Exception as e:
        exit_code = handle_api_error(e)
        raise typer.Exit(exit_code)


@app.command("delete")
def delete_flow(
    flow_id: str = typer.Argument(..., help="Flow ID (GUID)"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """
    Delete a Dataverse workflow.

    Examples:
        dataverse flow delete <flow-id>
        dataverse flow delete <flow-id> --yes
    """
    try:
        if not confirm:
            confirmed = typer.confirm(f"Are you sure you want to delete flow {flow_id}?")
            if not confirmed:
                print_error("Delete cancelled")
                raise typer.Exit(0)

        client = get_client()
        client.delete(f"workflows({flow_id})")
        print_success(f"Flow deleted successfully: {flow_id}")

    except Exception as e:
        exit_code = handle_api_error(e)
        raise typer.Exit(exit_code)


@app.command("activate")
def activate_flow(
    flow_id: str = typer.Argument(..., help="Flow ID (GUID)"),
):
    """
    Activate (turn on) a Dataverse workflow.

    Examples:
        dataverse flow activate <flow-id>
    """
    try:
        client = get_client()
        client.patch(f"workflows({flow_id})", {"statecode": 1})
        print_success(f"Flow activated successfully: {flow_id}")

    except Exception as e:
        exit_code = handle_api_error(e)
        raise typer.Exit(exit_code)


@app.command("deactivate")
def deactivate_flow(
    flow_id: str = typer.Argument(..., help="Flow ID (GUID)"),
):
    """
    Deactivate (turn off) a Dataverse workflow.

    Examples:
        dataverse flow deactivate <flow-id>
    """
    try:
        client = get_client()
        client.patch(f"workflows({flow_id})", {"statecode": 0})
        print_success(f"Flow deactivated successfully: {flow_id}")

    except Exception as e:
        exit_code = handle_api_error(e)
        raise typer.Exit(exit_code)
