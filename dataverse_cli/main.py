"""Main entry point for Dataverse CLI."""
import sys
import typer
from typing import Optional

from .client import ClientError

# Create main Typer app
app = typer.Typer(
    name="dataverse",
    help="CLI interface for Microsoft Dataverse - Manage workflows, solutions, entities, and more",
    no_args_is_help=True,
    add_completion=True,
)


# Import and register command modules
try:
    from .commands import flow, solution, auth, entity
    app.add_typer(flow.app, name="flow", help="Manage Dataverse workflows")
    app.add_typer(solution.app, name="solution", help="Manage Dataverse solutions")
    app.add_typer(auth.app, name="auth", help="Authentication and token utilities")
    app.add_typer(entity.app, name="entity", help="Query Dataverse entities/tables")
except ImportError:
    # Commands not yet implemented - will add as we build them
    pass


@app.callback()
def callback(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit",
        is_eager=True,
    ),
):
    """
    Dataverse CLI - Automate and manage Microsoft Dataverse from the command line.

    Authentication is handled via environment variables:

    Service Principal (Recommended):
      - DATAVERSE_URL
      - DATAVERSE_CLIENT_ID
      - DATAVERSE_CLIENT_SECRET
      - DATAVERSE_TENANT_ID

    User Authentication:
      - DATAVERSE_URL
      - DATAVERSE_CLIENT_ID
      - DATAVERSE_TENANT_ID
      - DATAVERSE_USERNAME
      - DATAVERSE_PASSWORD

    Examples:
        dataverse flow list --solution "Progress Content Automation"
        dataverse flow create --name "My New Flow" --trigger http
        dataverse solution list
        dataverse entity query workflows --filter "category eq 5"
    """
    if version:
        from . import __version__
        typer.echo(f"dataverse-cli version {__version__}")
        raise typer.Exit()


def main():
    """Main entry point for the CLI application."""
    try:
        app()
    except ClientError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(2)
    except KeyboardInterrupt:
        typer.echo("\nAborted!", err=True)
        raise typer.Exit(130)
    except Exception as e:
        typer.echo(f"Unexpected error: {e}", err=True)
        if "--debug" in sys.argv:
            raise
        raise typer.Exit(1)


if __name__ == "__main__":
    main()
