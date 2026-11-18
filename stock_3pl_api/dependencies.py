# Copyright 2024 Akretion (https://www.akretion.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from typing import Annotated

from fastapi import Depends, Security
from fastapi.security import APIKeyHeader

from odoo.api import Environment

from odoo.addons.fastapi.dependencies import fastapi_endpoint, odoo_env
from odoo.addons.fastapi.models.fastapi_endpoint import FastapiEndpoint
from odoo.addons.fastapi_auth_api_key.dependencies import authenticated_auth_api_key

# The logistics providers were integrated against the 17.0 endpoint and send the
# legacy "API-KEY" header, while fastapi_auth_api_key resolves its header name
# from FASTAPI_AUTH_HTTP_API_KEY_HEADER (default "HTTP-API-KEY"). The header name
# is therefore pinned here and the validation itself is delegated to the
# library: the key is looked up in auth.api.key and must belong to the key group
# of the endpoint. Nothing here reads the key value other than through the ORM.
LEGACY_API_KEY_HEADER = APIKeyHeader(name="API-KEY", auto_error=False)


def auth_env(
    key: Annotated[str, Security(LEGACY_API_KEY_HEADER)],
    env: Annotated[Environment, Depends(odoo_env)],
    endpoint: Annotated[FastapiEndpoint, Depends(fastapi_endpoint)],
) -> Environment:
    """Environment of the user owning the API key sent by the caller."""
    auth_api_key = authenticated_auth_api_key(key, env, endpoint)
    return auth_api_key.with_user(auth_api_key.user_id).env
