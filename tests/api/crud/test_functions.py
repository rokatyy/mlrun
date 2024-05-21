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
import sqlalchemy.orm

import mlrun.common.schemas
import server.api.crud


def test_set_function_deletion_task_id_updates_correctly(db: sqlalchemy.orm.Session):
    function_name = "test_function"
    function_tag = "latest"
    function = {
        "metadata": {"name": function_name, "tag": function_tag},
    }
    project = "test_project"
    deletion_task_id = "12345"

    server.api.crud.Functions().store_function(
        db, project=project, function=function, name=function_name, tag=function_tag
    )

    function = server.api.crud.Functions().get_function(
        db, name=function_name, project=project, tag=function_tag
    )

    result = server.api.crud.Functions().set_function_deletion_task_id(
        db_session=db,
        function=function,
        project=project,
        deletion_task_id=deletion_task_id,
    )

    assert result["status"]["deletion_task_id"] == deletion_task_id


def test_update_functions_with_api_gateway_url(db: sqlalchemy.orm.Session):
    function_name = "test_function"
    function_tag = "latest"
    function = {
        "metadata": {"name": function_name, "tag": function_tag},
    }
    project = "test_project"

    server.api.crud.Functions().store_function(
        db, project=project, function=function, name=function_name, tag=function_tag
    )
    server.api.utils.singletons.db.get_db().update_function(
        db,
        project=project,
        name=function_name,
        tag=function_tag,
        updates={"status.nuclio_name": function_name},
    )

    gw_host = "gw.example.com"
    api_gateway = mlrun.common.schemas.APIGateway(
        metadata=mlrun.common.schemas.APIGatewayMetadata(
            name="gw", namespace="default"
        ),
        spec=mlrun.common.schemas.APIGatewaySpec(
            name="gw",
            host=gw_host,
            upstreams=[
                mlrun.common.schemas.APIGatewayUpstream(
                    nucliofunction={"name": "test_function"}
                )
            ],
        ),
    )

    server.api.crud.Functions().update_functions_external_invocation_url(
        db, api_gateway, project
    )

    updated_function = server.api.crud.Functions().get_function(
        db, project=project, name=function_name, tag=function_tag
    )
    assert updated_function["status"]["external_invocation_urls"] == gw_host
