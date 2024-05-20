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
#
IMAGE_NAME_ENRICH_REGISTRY_PREFIX = "."  # prefix for image name to enrich with registry
MLRUN_CREATED_LABEL = "mlrun-created"
MLRUN_FUNCTIONS_LABEL = "mlrun-functions"
MLRUN_MODEL_CONF = "model-conf"
MLRUN_SERVING_SPEC_MOUNT_PATH = f"/tmp/mlrun/{MLRUN_MODEL_CONF}"
MLRUN_SERVING_SPEC_FILENAME = "serving_spec.json"
MLRUN_SERVING_SPEC_PATH = (
    f"{MLRUN_SERVING_SPEC_MOUNT_PATH}/{MLRUN_SERVING_SPEC_FILENAME}"
)
MYSQL_MEDIUMBLOB_SIZE_BYTES = 16 * 1024 * 1024
