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
from server.api.runtime_handlers import BaseRuntimeHandler


class RemoteRuntimeHandler(BaseRuntimeHandler):
    kind = "remote"
    class_modes = {RuntimeClassMode.run: "remote"}

    @staticmethod
    def _get_object_label_selector(object_id: str) -> str:
        pass

    def delete_resources(
            
        self,
        db: DBInterface,
        db_session: Session,
        label_selector: str = None,
        force: bool = False,
        grace_period: int = None,
    ):
        # TODO: add nuclio function deletion using async client
        super().delete_resources(db, db_session, label_selector, force, grace_period)
