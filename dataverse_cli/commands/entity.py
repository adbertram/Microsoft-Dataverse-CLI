"""Entity/table query commands for Dataverse CLI."""
import typer
from typing import Optional

from ..client import get_client
from ..output import (
    print_json,
    print_table,
    handle_api_error,
    format_response,
)

app = typer.Typer(help="Query Dataverse entities/tables")


@app.command("query")
def query_entity(
    entity_name: str = typer.Argument(..., help="Entity logical name (e.g., workflows, accounts)"),
    filter_query: Optional[str] = typer.Option(None, "--filter", "-f", help="OData filter expression"),
    select: Optional[str] = typer.Option(None, "--select", "-s", help="Comma-separated list of fields"),
    orderby: Optional[str] = typer.Option(None, "--orderby", "-o", help="Order by field"),
    top: Optional[int] = typer.Option(None, "--top", "-t", help="Limit number of results"),
    table_format: bool = typer.Option(False, "--table", help="Display as table"),
):
    """
    Query a Dataverse entity/table with OData filters.

    Examples:
        dataverse entity query workflows --filter "category eq 5"
        dataverse entity query workflows --filter "category eq 5" --select "name,workflowid" --top 10
        dataverse entity query accounts --filter "name eq 'Contoso'" --table
    """
    try:
        client = get_client()

        params = {}
        if filter_query:
            params["$filter"] = filter_query
        if select:
            params["$select"] = select
        if orderby:
            params["$orderby"] = orderby
        if top:
            params["$top"] = top

        result = client.get(entity_name, params=params)
        data = format_response(result)

        if table_format and isinstance(data, list) and data:
            # Get column names from first record
            columns = list(data[0].keys())
            # Limit to reasonable number of columns
            if len(columns) > 6:
                columns = columns[:6]
            print_table(data, columns)
        else:
            print_json(data)

    except Exception as e:
        exit_code = handle_api_error(e)
        raise typer.Exit(exit_code)


@app.command("get")
def get_record(
    entity_name: str = typer.Argument(..., help="Entity logical name (e.g., workflows)"),
    record_id: str = typer.Argument(..., help="Record ID (GUID)"),
    select: Optional[str] = typer.Option(None, "--select", "-s", help="Comma-separated list of fields"),
):
    """
    Get a specific record by ID.

    Examples:
        dataverse entity get workflows 29e2253b-cabc-f011-bbd3-000d3a8ba54e
        dataverse entity get workflows 29e2253b-cabc-f011-bbd3-000d3a8ba54e --select "name,statecode"
    """
    try:
        client = get_client()

        params = {}
        if select:
            params["$select"] = select

        result = client.get(f"{entity_name}({record_id})", params=params)
        formatted = format_response(result)
        print_json(formatted)

    except Exception as e:
        exit_code = handle_api_error(e)
        raise typer.Exit(exit_code)


@app.command("count")
def count_records(
    entity_name: str = typer.Argument(..., help="Entity logical name"),
    filter_query: Optional[str] = typer.Option(None, "--filter", "-f", help="OData filter expression"),
):
    """
    Count records in an entity/table.

    Examples:
        dataverse entity count workflows
        dataverse entity count workflows --filter "category eq 5"
    """
    try:
        client = get_client()

        params = {"$count": "true", "$top": 1}
        if filter_query:
            params["$filter"] = filter_query

        result = client.get(entity_name, params=params)

        count = result.get("@odata.count", 0)
        print_json({"entity": entity_name, "count": count})

    except Exception as e:
        exit_code = handle_api_error(e)
        raise typer.Exit(exit_code)


@app.command("metadata")
def get_entity_metadata(
    entity_name: str = typer.Argument(..., help="Entity logical name"),
):
    """
    Get metadata for an entity/table.

    Examples:
        dataverse entity metadata workflow
        dataverse entity metadata account
    """
    try:
        client = get_client()

        # Query EntityDefinitions for metadata
        params = {
            "$filter": f"LogicalName eq '{entity_name}'",
            "$select": "LogicalName,DisplayName,PrimaryIdAttribute,PrimaryNameAttribute,EntitySetName"
        }

        result = client.get("EntityDefinitions", params=params)
        formatted = format_response(result)

        if isinstance(formatted, list) and formatted:
            print_json(formatted[0])
        else:
            print_json(formatted)

    except Exception as e:
        exit_code = handle_api_error(e)
        raise typer.Exit(exit_code)
