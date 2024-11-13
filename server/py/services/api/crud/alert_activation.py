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

import datetime

import mlrun.utils.singleton


class AlertActivation(
    metaclass=mlrun.utils.singleton.Singleton,
):
    def list_alert_activations(
        self,
        session: sqlalchemy.orm.Session,
        project: Optional[str],
        name: Optional[str] = None,
        start: Optional[datetime.datetime] = None,
        end: Optional[datetime.datetime] = None,
        entity: Optional[str] = None,
        severity: Optional[list[str]] = None,
        page=page,
        page_size=page_size,
    ) -> list[mlrun.common.schemas.AlertActivation]:
        project = project or mlrun.mlconf.default_project
        return framework.utils.singletons.db.get_db().list_alerts_activations(
            session=session,
            project=project,
            name=name,
            start=start,
            end=end,
            entity=entity,
            severity=severity,
            page=page,
            page_size=page_size,
        )
