"""Authentication commands for Dataverse CLI."""
import typer
from msal import ConfidentialClientApplication, PublicClientApplication

from ..config import get_config
from ..output import print_success, print_error, print_json, handle_api_error

app = typer.Typer(help="Authentication and token utilities")


@app.command("test")
def test_auth():
    """
    Test authentication configuration and get an access token.

    This command attempts to authenticate using the configured credentials
    and displays the result without making any API calls.

    Examples:
        dataverse auth test
    """
    try:
        config = get_config()

        # Check for missing credentials
        missing = config.get_missing_credentials()
        if missing:
            print_error("Missing required credentials:")
            for cred in missing:
                print_error(f"  - {cred}")
            raise typer.Exit(1)

        # Try to get a token
        if config.has_service_principal_auth():
            print_json({"auth_method": "service_principal", "client_id": config.client_id})
            authority = f"https://login.microsoftonline.com/{config.tenant_id}"
            app = ConfidentialClientApplication(
                config.client_id,
                authority=authority,
                client_credential=config.client_secret,
            )

            scope = [config.get_auth_scope()]
            result = app.acquire_token_for_client(scopes=scope)

            if "access_token" in result:
                print_success("Authentication successful!")
                print_json({
                    "token_type": result.get("token_type"),
                    "expires_in": result.get("expires_in"),
                    "scope": config.get_auth_scope()
                })
            else:
                error = result.get("error_description", result.get("error", "Unknown error"))
                print_error(f"Authentication failed: {error}")
                raise typer.Exit(1)

        elif config.has_user_auth():
            print_json({"auth_method": "user_credentials", "username": config.username})
            authority = f"https://login.microsoftonline.com/{config.tenant_id}"
            app = PublicClientApplication(
                config.client_id,
                authority=authority,
            )

            scope = [config.get_auth_scope()]
            result = app.acquire_token_by_username_password(
                config.username,
                config.password,
                scopes=scope
            )

            if "access_token" in result:
                print_success("Authentication successful!")
                print_json({
                    "token_type": result.get("token_type"),
                    "expires_in": result.get("expires_in"),
                    "scope": config.get_auth_scope()
                })
            else:
                error = result.get("error_description", result.get("error", "Unknown error"))
                print_error(f"Authentication failed: {error}")
                raise typer.Exit(1)

        elif config.has_token_auth():
            print_json({"auth_method": "access_token"})
            print_success("Using provided access token")

        else:
            print_error("No valid authentication method configured")
            raise typer.Exit(1)

    except Exception as e:
        exit_code = handle_api_error(e)
        raise typer.Exit(exit_code)


@app.command("token")
def get_token(
    show_token: bool = typer.Option(False, "--show", help="Display the full access token"),
):
    """
    Get an access token for Dataverse API access.

    Examples:
        dataverse auth token
        dataverse auth token --show
    """
    try:
        config = get_config()

        # Check for missing credentials
        missing = config.get_missing_credentials()
        if missing:
            print_error("Missing required credentials:")
            for cred in missing:
                print_error(f"  - {cred}")
            raise typer.Exit(1)

        # Get token based on authentication method
        access_token = None

        if config.has_token_auth():
            access_token = config.access_token
            print_success("Using configured access token")

        elif config.has_service_principal_auth():
            authority = f"https://login.microsoftonline.com/{config.tenant_id}"
            app = ConfidentialClientApplication(
                config.client_id,
                authority=authority,
                client_credential=config.client_secret,
            )

            scope = [config.get_auth_scope()]
            result = app.acquire_token_for_client(scopes=scope)

            if "access_token" in result:
                access_token = result["access_token"]
                print_success("Token acquired successfully (service principal)")
            else:
                error = result.get("error_description", result.get("error", "Unknown error"))
                print_error(f"Failed to acquire token: {error}")
                raise typer.Exit(1)

        elif config.has_user_auth():
            authority = f"https://login.microsoftonline.com/{config.tenant_id}"
            app = PublicClientApplication(
                config.client_id,
                authority=authority,
            )

            scope = [config.get_auth_scope()]
            result = app.acquire_token_by_username_password(
                config.username,
                config.password,
                scopes=scope
            )

            if "access_token" in result:
                access_token = result["access_token"]
                print_success("Token acquired successfully (user credentials)")
            else:
                error = result.get("error_description", result.get("error", "Unknown error"))
                print_error(f"Failed to acquire token: {error}")
                raise typer.Exit(1)

        if show_token:
            print_json({"access_token": access_token})
        else:
            print_json({
                "message": "Token acquired successfully",
                "hint": "Use --show to display the full token"
            })

    except Exception as e:
        exit_code = handle_api_error(e)
        raise typer.Exit(exit_code)


@app.command("whoami")
def whoami():
    """
    Display information about the current authenticated user/service principal.

    Examples:
        dataverse auth whoami
    """
    try:
        from ..client import get_client

        client = get_client()

        # Make a request to WhoAmI function
        result = client.get("WhoAmI()")

        print_success("Authentication verified!")
        print_json(result)

    except Exception as e:
        exit_code = handle_api_error(e)
        raise typer.Exit(exit_code)
