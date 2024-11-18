# Copyright 2024 Iguazio
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import mlrun.common.schemas

from typing import Optional

import framework.utils.auth.verifier
import framework.utils.clients.chief
import framework.utils.singletons.project_member
import services.api.crud
from framework.api import deps

router = APIRouter(prefix="/projects/{project}/alerts")


@router.get(
    "/activations",
)
async def list_alert_activations(
    project: str,
    name: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    entity: Optional[str] = None,
    severity: Optional[list[str]] = None,
    page: int = Query(None, gt=0),
    page_size: int = Query(None, alias="page-size", gt=0),
    page_token: str = Query(None, alias="page-token"),
    auth_info: mlrun.common.schemas.AuthInfo = Depends(deps.authenticate_request),
    db_session: Session = Depends(deps.get_db_session),
):
    allowed_project_names = (
        await services.api.crud.Projects().list_allowed_project_names(
            db_session, auth_info, project=project
        )
    )
    paginator = services.api.utils.pagination.Paginator()

    async def _filter_alert_activations_by_permissions(_alert_activations):
        return await framework.utils.auth.verifier.AuthVerifier().filter_project_resources_by_permissions(
            mlrun.common.schemas.AuthorizationResourceTypes.alert_activations,
            _alert_activations,
            lambda alert_activation: (
                alert_activation.project,
                alert_activation.name,
            ),
            auth_info,
        )

    activations, page_info = await paginator.paginate_permission_filtered_request(
        db_session,
        services.api.crud.AlertActivation().list_alert_activations,
        _filter_alert_activations_by_permissions,
        auth_info,
        token=page_token,
        page=page,
        page_size=page_size,
        project=allowed_project_names,
        name=name,
        start=mlrun.utils.datetime_from_iso(start),
        end=mlrun.utils.datetime_from_iso(end),
        entity=entity,
        severity=severity,
    )

    return {
        "activations": activations,
        "pagination": page_info,
    }
