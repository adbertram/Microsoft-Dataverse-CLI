"""Solution commands for Dataverse CLI."""
import typer
from typing import Optional

from ..client import get_client
from ..output import (
    print_json,
    print_table,
    print_success,
    handle_api_error,
    format_response,
)

app = typer.Typer(help="Manage Dataverse solutions")


@app.command("list")
def list_solutions(
    managed: Optional[bool] = typer.Option(None, "--managed", help="Filter by managed solutions"),
    table_format: bool = typer.Option(False, "--table", "-t", help="Display as table"),
):
    """
    List all Dataverse solutions.

    Examples:
        dataverse solution list
        dataverse solution list --managed
        dataverse solution list --table
    """
    try:
        client = get_client()

        params = {
            "$select": "solutionid,friendlyname,uniquename,version,ismanaged,installedon",
            "$orderby": "friendlyname"
        }

        if managed is not None:
            params["$filter"] = f"ismanaged eq {str(managed).lower()}"

        result = client.get("solutions", params=params)
        solutions = format_response(result)

        if table_format and isinstance(solutions, list):
            # Format managed status for display
            for solution in solutions:
                solution["managed"] = "Yes" if solution.get("ismanaged") else "No"

            print_table(solutions, ["friendlyname", "uniquename", "version", "managed"])
        else:
            print_json(solutions)

    except Exception as e:
        exit_code = handle_api_error(e)
        raise typer.Exit(exit_code)


@app.command("get")
def get_solution(
    solution_id: Optional[str] = typer.Option(None, "--id", help="Solution ID (GUID)"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Solution friendly name"),
):
    """
    Get detailed information about a specific solution.

    Examples:
        dataverse solution get --id <solution-guid>
        dataverse solution get --name "Progress Content Automation"
    """
    try:
        client = get_client()

        if solution_id:
            result = client.get(f"solutions({solution_id})")
            formatted = format_response(result)
            print_json(formatted)
        elif name:
            params = {
                "$filter": f"friendlyname eq '{name}'"
            }
            result = client.get("solutions", params=params)
            formatted = format_response(result)
            if isinstance(formatted, list) and formatted:
                print_json(formatted[0])
            else:
                print_json(formatted)
        else:
            typer.echo("Error: Either --id or --name must be provided", err=True)
            raise typer.Exit(1)

    except Exception as e:
        exit_code = handle_api_error(e)
        raise typer.Exit(exit_code)


@app.command("components")
def list_solution_components(
    solution_id: Optional[str] = typer.Option(None, "--id", help="Solution ID (GUID)"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Solution friendly name"),
    component_type: Optional[str] = typer.Option(None, "--type", "-t", help="Component type filter"),
):
    """
    List components in a solution (flows, entities, etc.).

    Examples:
        dataverse solution components --name "Progress Content Automation"
        dataverse solution components --id <solution-guid>
    """
    try:
        client = get_client()

        # Get solution ID if name provided
        if name and not solution_id:
            params = {"$filter": f"friendlyname eq '{name}'", "$select": "solutionid"}
            result = client.get("solutions", params=params)
            solutions = format_response(result)
            if isinstance(solutions, list) and solutions:
                solution_id = solutions[0].get("solutionid")
            else:
                typer.echo(f"Error: Solution '{name}' not found", err=True)
                raise typer.Exit(1)

        if not solution_id:
            typer.echo("Error: Either --id or --name must be provided", err=True)
            raise typer.Exit(1)

        params = {
            "$filter": f"_solutionid_value eq {solution_id}",
            "$select": "solutioncomponentid,componenttype,objectid,createdon"
        }

        result = client.get("solutioncomponents", params=params)
        components = format_response(result)

        print_json(components)

    except Exception as e:
        exit_code = handle_api_error(e)
        raise typer.Exit(exit_code)


@app.command("flows")
def list_solution_flows(
    solution_id: Optional[str] = typer.Option(None, "--id", help="Solution ID (GUID)"),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Solution friendly name"),
    table_format: bool = typer.Option(False, "--table", "-t", help="Display as table"),
):
    """
    List all flows in a specific solution.

    Examples:
        dataverse solution flows --name "Progress Content Automation"
        dataverse solution flows --id <solution-guid> --table
    """
    try:
        client = get_client()

        # Get solution ID if name provided
        if name and not solution_id:
            params = {"$filter": f"friendlyname eq '{name}'", "$select": "solutionid"}
            result = client.get("solutions", params=params)
            solutions = format_response(result)
            if isinstance(solutions, list) and solutions:
                solution_id = solutions[0].get("solutionid")
            else:
                typer.echo(f"Error: Solution '{name}' not found", err=True)
                raise typer.Exit(1)

        if not solution_id:
            typer.echo("Error: Either --id or --name must be provided", err=True)
            raise typer.Exit(1)

        # First, get workflow component IDs from solution components
        # componenttype = 29 is for workflows
        component_params = {
            "$filter": f"_solutionid_value eq {solution_id} and componenttype eq 29",
            "$select": "objectid"
        }

        component_result = client.get("solutioncomponents", params=component_params)
        components = format_response(component_result)

        if not components:
            flows = []
        else:
            # Extract workflow IDs
            workflow_ids = [comp.get("objectid") for comp in components if comp.get("objectid")]

            if not workflow_ids:
                flows = []
            else:
                # Query workflows with these IDs
                # Build filter: workflowid eq 'id1' or workflowid eq 'id2' ...
                id_filters = " or ".join([f"workflowid eq {wid}" for wid in workflow_ids])
                params = {
                    "$filter": f"category eq 5 and ({id_filters})",
                    "$select": "workflowid,name,statecode,createdon,modifiedon",
                    "$orderby": "modifiedon desc"
                }

                result = client.get("workflows", params=params)
                flows = format_response(result)

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
