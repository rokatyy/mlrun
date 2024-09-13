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
import subprocess
from typing import Any, Dict, List, Optional, Union

import mlrun.common.schemas
from mlrun.utils import logger


class NIM:
    def __init__(
            self,
            model: str,
            NGC_API_KEY: str,
            project_name: str,
            image_name: Optional[str],
            node_selection: Optional[Dict] = None,
            skip_deploy: Optional[bool] = True,
            ignore_secret_creation_errors: Optional[bool] = True,
            authentication_mode: mlrun.common.schemas.APIGatewayAuthenticationMode = mlrun.common.schemas.APIGatewayAuthenticationMode.none,
            authentication_creds: tuple[str, str] = None,
            **invocation_kwargs,
    ):
        self.model = model
        self.image_name = image_name or f"nvcr.io/nim/{model}:latest"
        self._NGC_API_KEY = NGC_API_KEY
        self.project = mlrun.get_or_create_project(project_name)
        self.docker_creds_secret_name = (
            f"{self.project.name}-{self.model}-nim-creds".replace("/", "-")
        )
        self.ngc_secret_name = f"{self.project.name}-{self.model}-ngc-api-key".replace(
            "/", "-"
        )
        self.application = None
        self.node_selection = node_selection
        self.ignore_secret_creation_errors = ignore_secret_creation_errors
        self.application_name = self.model.replace("/", "-")
        self.api_gateway_name = f"{self.application_name}-gw"
        self.authentication_mode = authentication_mode
        self._authentication_creds = authentication_creds

        # Dynamically assign each kwarg to an instance variable
        self.invocation_kwargs = invocation_kwargs
        if not skip_deploy:
            self.deploy()
        else:
            self.application = self.project.get_function(
                self.application_name, ignore_cache=True
            )
            if self.is_deployed():
                logger.info(
                    f"Found deployed application. Status: {self.application.status.to_json()}"
                )

    def deploy(self, with_api_gateway: bool = True):
        self.create_secrets()
        self.deploy_application()
        if with_api_gateway:
            self.create_api_gateway(
                name=self.api_gateway_name,
                direct_port_access=True,
                authentication_mode=self.authentication_mode,
                authentication_creds=self._authentication_creds,
            )

    def deploy_application(self):
        application = self.project.set_function(
            name=self.application_name, kind="application", image=self.image_name
        )
        application.set_internal_application_port(port=8000)
        application.set_env_from_secret(secret=self.ngc_secret_name, name="NGC_API_KEY")
        application.spec.env.append(
            {
                "name": "LD_LIBRARY_PATH",
                "value": "/usr/local/lib/python3.10/dist-packages/tensorrt_llm/libs:"
                         "/usr/local/lib/python3.10/dist-packages/nvidia/cublas/lib:"
                         "/usr/local/lib/python3.10/dist-packages/tensorrt_libs",
            }
        )
        application.set_image_pull_configuration(
            image_pull_secret_name=self.docker_creds_secret_name
        )
        if self.node_selection:
            application.with_node_selection(node_selector=self.node_selection)
        application.deploy(create_default_api_gateway=False)
        self.application = application

    def is_deployed(self):
        return self.application is not None

    def create_api_gateway(
            self,
            name: str = None,
            path: str = None,
            direct_port_access: bool = False,
            authentication_mode: mlrun.common.schemas.APIGatewayAuthenticationMode = None,
            authentication_creds: tuple[str, str] = None,
            ssl_redirect: bool = None,
            set_as_default: bool = False,
    ):
        """
        Create the application API gateway. Once the application is deployed, the API gateway can be created.
        An application without an API gateway is not accessible.
        :param name:                    The name of the API gateway, defaults to <function-name>-<function-tag>
        :param path:                    Optional path of the API gateway, default value is "/"
        :param direct_port_access:      Set True to allow direct port access to the application sidecar
        :param authentication_mode:     API Gateway authentication mode
        :param authentication_creds:    API Gateway basic authentication credentials as a tuple (username, password)
        :param ssl_redirect:            Set True to force SSL redirect, False to disable. Defaults to
                                        mlrun.mlconf.force_api_gateway_ssl_redirect()
        :param set_as_default:          Set the API gateway as the default for the application (`status.api_gateway`)

        :return:    The API gateway URL
        """
        if not self.is_deployed():
            raise "API gateway can not be created - Application not deployed"

        if not name:
            name = self.api_gateway_name

        self.application.create_api_gateway(
            name=name,
            path=path,
            direct_port_access=direct_port_access,
            authentication_mode=authentication_mode,
            authentication_creds=authentication_creds,
            ssl_redirect=ssl_redirect,
            set_as_default=set_as_default,
        )

        self.application._sync_api_gateway()
        api_gateway = self.project.get_api_gateway(name)
        self.application.api_gateway = api_gateway

    def create_secrets(self):
        self._create_docker_creds_secret()
        self._create_secret_with_api_key()

    def _create_docker_creds_secret(self):
        # Command which creates a secret to pull NIM image
        command = [
            "kubectl",
            "create",
            "secret",
            "docker-registry",
            self.docker_creds_secret_name,
            "--docker-server=nvcr.io",
            r"--docker-username=\$oauthtoken",
            f"--docker-password={self._NGC_API_KEY}",
            "--namespace=default-tenant",
        ]
        self._execute(command, self.ignore_secret_creation_errors)

    def _create_secret_with_api_key(self):
        command = [
            "kubectl",
            "create",
            "secret",
            "generic",
            self.ngc_secret_name,
            f"--from-literal=NGC_API_KEY={self._NGC_API_KEY}",
            "--namespace=default-tenant",
        ]
        self._execute(command, self.ignore_secret_creation_errors)

    @staticmethod
    def _execute(command: list[str], ignore_error: bool):
        result = subprocess.run(
            " ".join(command), shell=True, capture_output=True, text=True
        )
        if result.returncode != 0:
            error = f"Failed to execute command: {result.stderr}"
            if not ignore_error:
                raise Exception(error)
            else:
                logger.error(error)

    def invoke(
            self, messages: Union[str, Dict[str, Any], List[Dict[str, Any]]], **kwargs
    ):
        # Normalize messages to a list of dictionaries
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        elif isinstance(messages, dict):
            messages = [messages]
        elif not isinstance(messages, list):
            raise TypeError("Messages should be a string, dict, or list of dicts")

        if not self.application:
            raise Exception("Application isn't deployed")
        body = self._generate_invoke_data(messages, **kwargs)
        return self._invoke(body)

    def _invoke(self, body):
        return self.application.invoke(
            path="/v1/chat/completions", body=body, method="POST"
        )

    def _generate_invoke_data(self, messages, **kwargs):
        invocation_params = {**self.invocation_kwargs, **kwargs}

        # Initialize the data dictionary with the mandatory fields
        data = {
            "model": self.model,
            "messages": messages,
        }

        # Dynamically add all other key-values from invocation_params
        for key, value in invocation_params.items():
            data[key] = value
        return data
