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
from kfp import dsl

funcs = {}


@dsl.pipeline(name="Example pipeline", description="some pipeline description.")
def kfpipeline():
    # analyze our dataset
    funcs["describe"].as_step(
        name="summary",
        params={"label_column": "labels"},
    )

    # train with hyper-paremeters
    funcs["trainer-function"].as_step(
        name="trainer-function",
    )
