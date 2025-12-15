from typing import Annotated

from fastapi import Depends, Security
from fastapi.security import APIKeyHeader

from odoo.api import Environment

# Enforce "API-KEY" header matching V12 spec exactly
# fastapi_auth_api_key uses HTTP-API-KEY by default or ENV var.
# Using Security() allows it to appear in Swagger UI correctly.
API_KEY_HEADER = APIKeyHeader(name="API-KEY", auto_error=True)


def api_key_auth_env(
    api_key: str = Security(API_KEY_HEADER),
) -> Environment:
    """Wrapper to force API-KEY header name but reuse logic"""
    # Pass the key to the library logic manually if needed,
    # but here we rely on the fact that authenticated_env_by_auth_api_key
    # usually inspects the request.
    # However, to be explicit and reuse code:
    pass


# We redefine the dependency to explicitly use the header name "API-KEY"
# The standard module reads os.environ.get("FASTAPI_AUTH_HTTP_API_KEY_HEADER", "HTTP-API-KEY")
# Since we cannot easily guarantee the env var is set on the server, we define a local dependency.

from fastapi import HTTPException, status

from odoo import SUPERUSER_ID

from odoo.addons.fastapi.dependencies import fastapi_endpoint, odoo_env
from odoo.addons.fastapi.models.fastapi_endpoint import FastapiEndpoint


def auth_env(
    key: Annotated[str, Security(API_KEY_HEADER)],
    env: Annotated[Environment, Depends(odoo_env)],
    endpoint: Annotated[FastapiEndpoint, Depends(fastapi_endpoint)],
) -> Environment:
    admin_env = Environment(env.cr, SUPERUSER_ID, {})
    try:
        # Re-using logic from auth_api_key module
        auth_api_key = admin_env["auth.api.key"]._retrieve_api_key(key)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    # Check Endpoint Group Authorization
    if (
        endpoint.sudo().auth_api_key_group_id
        and auth_api_key not in endpoint.sudo().auth_api_key_group_id.auth_api_key_ids
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized API Key for this endpoint",
        )

    return auth_api_key.with_user(auth_api_key.user_id).env
