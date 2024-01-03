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
import asyncio
import datetime
import traceback
import typing
import uuid

import fastapi
import fastapi.concurrency
import sqlalchemy.orm

import mlrun.common.schemas
import mlrun.errors
import mlrun.utils.singleton
import server.api.utils.helpers
import server.api.utils.singletons.db
import server.api.utils.singletons.project_member
from mlrun.utils import logger


class ProjectBackgroundTasksHandler(metaclass=mlrun.utils.singleton.Singleton):
    def create_background_task(
        self,
        db_session: sqlalchemy.orm.Session,
        project: str,
        background_tasks: fastapi.BackgroundTasks,
        function,
        timeout: int = None,  # in seconds
        name: str = None,
        *args,
        **kwargs,
    ) -> mlrun.common.schemas.BackgroundTask:
        name = name or str(uuid.uuid4())
        logger.debug(
            "Creating background task",
            name=name,
            project=project,
            function=function.__name__,
        )
        server.api.utils.singletons.db.get_db().store_background_task(
            db_session,
            name,
            project,
            mlrun.common.schemas.BackgroundTaskState.running,
            timeout,
        )
        background_tasks.add_task(
            self.background_task_wrapper,
            db_session,
            project,
            name,
            function,
            *args,
            **kwargs,
        )
        return self.get_background_task(db_session, name, project)

    def get_background_task(
        self,
        db_session: sqlalchemy.orm.Session,
        name: str,
        project: str,
    ) -> mlrun.common.schemas.BackgroundTask:
        return server.api.utils.singletons.db.get_db().get_background_task(
            db_session, name, project, background_task_exceeded_timeout
        )

    async def background_task_wrapper(
        self,
        db_session: sqlalchemy.orm.Session,
        project: str,
        name: str,
        function,
        *args,
        **kwargs,
    ):
        try:
            if asyncio.iscoroutinefunction(function):
                await function(*args, **kwargs)
            else:
                await fastapi.concurrency.run_in_threadpool(function, *args, **kwargs)
        except Exception as exc:
            err_str = mlrun.errors.err_to_str(exc)
            logger.warning(
                "Background task execution failed",
                function_name=function.__name__,
                exc=err_str,
                tb=traceback.format_exc(),
            )
            server.api.utils.singletons.db.get_db().store_background_task(
                db_session,
                name,
                project=project,
                state=mlrun.common.schemas.BackgroundTaskState.failed,
                error=err_str,
            )
        else:
            server.api.utils.singletons.db.get_db().store_background_task(
                db_session,
                name,
                project=project,
                state=mlrun.common.schemas.BackgroundTaskState.succeeded,
            )


class InternalBackgroundTasksHandler(metaclass=mlrun.utils.singleton.Singleton):
    def __init__(self):
        self._internal_background_tasks: typing.Dict[
            str, mlrun.common.schemas.BackgroundTask
        ] = {}

    @server.api.utils.helpers.ensure_running_on_chief
    def create_background_task(
        self,
        background_tasks: fastapi.BackgroundTasks,
        function,
        name: str = None,
        timeout: int = None,  # in seconds
        *args,
        **kwargs,
    ) -> mlrun.common.schemas.BackgroundTask:
        name = name or str(uuid.uuid4())
        # sanity
        if name in self._internal_background_tasks:
            raise RuntimeError("Background task name already exists")
        background_task = self._generate_background_task(name)
        if timeout and mlrun.mlconf.background_tasks.timeout_mode == "enabled":
            background_task.metadata.timeout = int(timeout)
        self._internal_background_tasks[name] = background_task
        background_tasks.add_task(
            self.background_task_wrapper,
            name=name,
            function=function,
            *args,
            **kwargs,
        )

        return self.get_background_task(name)

    @server.api.utils.helpers.ensure_running_on_chief
    def get_background_task(
        self,
        name: str,
        raise_on_not_found: bool = False,
    ) -> mlrun.common.schemas.BackgroundTask:
        """
        :return: returns the background task object and bool whether exists
        """
        if name in self._internal_background_tasks:
            background_task = self._internal_background_tasks[name]
            if background_task_exceeded_timeout(
                background_task.metadata.created,
                background_task.metadata.timeout,
                background_task.status.state,
            ):
                self._update_background_task(
                    name,
                    mlrun.common.schemas.BackgroundTaskState.failed,
                    error="Timeout exceeded",
                )
            return self._internal_background_tasks[name]
        elif raise_on_not_found:
            raise mlrun.errors.MLRunNotFoundError(f"Background task {name} not found")
        else:
            return self._generate_background_task_not_found_response(name)

    @server.api.utils.helpers.ensure_running_on_chief
    async def background_task_wrapper(self, name: str, function, *args, **kwargs):
        try:
            if asyncio.iscoroutinefunction(function):
                await function(*args, **kwargs)
            else:
                await fastapi.concurrency.run_in_threadpool(function, *args, **kwargs)

        except Exception as exc:
            err_str = mlrun.errors.err_to_str(exc)
            logger.warning(
                "Background task execution failed",
                function_name=function.__name__,
                exc=err_str,
                tb=traceback.format_exc(),
            )
            self._update_background_task(
                name, mlrun.common.schemas.BackgroundTaskState.failed, error=err_str
            )
        else:
            self._update_background_task(
                name, mlrun.common.schemas.BackgroundTaskState.succeeded
            )

    def _update_background_task(
        self,
        name: str,
        state: mlrun.common.schemas.BackgroundTaskState,
        error: typing.Optional[str] = None,
    ):
        background_task = self._internal_background_tasks[name]
        background_task.status.state = state
        background_task.status.error = error
        background_task.metadata.updated = datetime.datetime.utcnow()

    @staticmethod
    def _generate_background_task_not_found_response(
        name: str, project: typing.Optional[str] = None
    ):
        # in order to keep things simple we don't persist the internal background tasks to the DB
        # If for some reason get is called and the background task doesn't exist, it means that probably we got
        # restarted, therefore we want to return a failed background task so the client will retry (if needed)
        return mlrun.common.schemas.BackgroundTask(
            metadata=mlrun.common.schemas.BackgroundTaskMetadata(
                name=name, project=project
            ),
            spec=mlrun.common.schemas.BackgroundTaskSpec(),
            status=mlrun.common.schemas.BackgroundTaskStatus(
                state=mlrun.common.schemas.BackgroundTaskState.failed,
                error="Background task not found",
            ),
        )

    @staticmethod
    def _generate_background_task(
        name: str, project: typing.Optional[str] = None
    ) -> mlrun.common.schemas.BackgroundTask:
        now = datetime.datetime.utcnow()
        metadata = mlrun.common.schemas.BackgroundTaskMetadata(
            name=name,
            project=project,
            created=now,
            updated=now,
        )
        spec = mlrun.common.schemas.BackgroundTaskSpec()
        status = mlrun.common.schemas.BackgroundTaskStatus(
            state=mlrun.common.schemas.BackgroundTaskState.running
        )
        return mlrun.common.schemas.BackgroundTask(
            metadata=metadata, spec=spec, status=status
        )


def background_task_exceeded_timeout(start_time, timeout, task_state) -> bool:
    # We don't verify if timeout_mode is enabled because if timeout is defined and
    # mlrun.mlconf.background_tasks.timeout_mode == "disabled",
    # it signifies that the background task was initiated while timeout mode was enabled,
    # and we intend to verify it as if timeout mode was enabled
    if (
        timeout
        and task_state not in mlrun.common.schemas.BackgroundTaskState.terminal_states()
        and datetime.datetime.utcnow()
        > datetime.timedelta(seconds=int(timeout)) + start_time
    ):
        return True
    return False
