# Copyright 2023 Iguazio
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
import base64
from typing import Union
import urllib.parse
import requests


class APIGateway:
    def __init__(
        self,
        project,
        name: str,
        host: str,
        path: str,
        description: str,
        functions: list[str],
        username: Union[None, str],
        password: Union[None, str],
        canary: Union[dict[str, int], None],
    ):
        self.project = project
        self.name = name
        self.host = host
        self.functions = functions
        self.path = path
        self.description = description
        self.canary = canary
        self._auth = None
        self._invoke_url = self._generate_invoke_url() if not host else host
        self._generate_auth(username, password)

    def invoke(self):
        headers = {} if not self._auth else {"Authorization": self._auth}
        return requests.post(self._invoke_url, headers=headers)

    def _generate_auth(self, username: Union[None, str], password: Union[None, str]):
        if username and password:
            token = base64.b64encode(f"{username}:{password}")
            self._auth = f"Basic {token}"

    def requires_auth(self):
        return self._auth is not None

    def _generate_invoke_url(self):
        nuclio_hostname = urllib.parse.urlparse(
            self.mlrun.mlconf.nuclio_dashboard_url
        ).netloc
        # cut nuclio prefix
        common_hostname = nuclio_hostname[nuclio_hostname.find(".") + 1 :]
        return urllib.parse.urljoin(
            f"{self.name}-{self.project}.{common_hostname}", self.path
        )


def new_api_gateway(
    project,
    name: str,
    host: str,
    path: str,
    description: str,
    functions: list[str],
    username: Union[None, str],
    password: Union[None, str],
    canary: Union[dict[str, int], None],
) -> APIGateway:
    if not name:
        raise ValueError("API Gateway name cannot be empty")

    if canary:
        for func in functions:
            if func not in canary:
                raise ValueError(
                    f"Canary object doesn't contain percent value for function {func}"
                )
        if sum(canary.values()) != 100:
            raise ValueError(
                f"Th sum of canary function percents should be equal to 100"
            )
    return APIGateway(
        project=project,
        name=name,
        host=host,
        path=path,
        description=description,
        functions=functions,
        username=username,
        password=password,
        canary=canary,
    )
