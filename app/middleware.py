import json
import logging
import time
from typing import Callable
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message


class RouterLoggingMiddleware(BaseHTTPMiddleware):
    """
    Overview:
        The BaseHTTPMiddleware class provides a basic structure for creating middleware in FastAPI
        It has a dispatch method which responsible for handling the flow of incoming requests and outgoing responses
        The dispatch method takes in two arguments: request and call_next
            request contains information about the incoming request such as the headers, query parameters, and the body
            call_next is a callable that will pass the request on to the next middleware in the stack or to the final endpoint handler
    """

    def __init__(self, app: FastAPI, *, logger: logging.Logger) -> None:
        self._logger = logger
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id: str = str(uuid4())
        logging_dict = {'X-API-REQUEST-ID': request_id}  # X-API-REQUEST-ID maps each request-response to a unique ID

        await self.set_body(request)
        response, response_dict = await self._log_response(call_next, request, request_id)
        request_dict = await self._log_request(request)
        logging_dict["request"] = request_dict
        logging_dict["response"] = response_dict

        self._logger.info(logging_dict)

        return response

    async def set_body(self, request: Request):
        """
        Overview:
            Avails the response body to be logged within a middleware as it is generally not a standard practice
        Arguments:
            - request: Request
        Returns:
            - receive_: Receive
        """
        receive_ = await request._receive()
        async def receive() -> Message: return receive_
        request._receive = receive

    async def _log_request(self, request: Request) -> str:
        """
        Arguments:
            - request: Request
        """
        path = request.url.path
        if request.query_params:
            path += f"?{request.query_params}"

        request_logging = {
            "method": request.method,
            "path": path,
            "ip": request.client.host,
            "headers": request.headers
        }

        try:
            body = await request.form()
            request_logging["data"] = body
        except BaseException:
            body = None

        return request_logging

    async def _log_response(self, call_next: Callable, request: Request, request_id: str) -> Response:
        """
        Arguments:
            - call_next: Callable (To execute the actual path function and get response back)
            - request: Request
            - request_id: str (uuid)
        Returns:
            - response: Response
            - response_logging: str
        """

        start_time = time.perf_counter()
        response = await self._execute_request(call_next, request, request_id)
        finish_time = time.perf_counter()

        overall_status = "successful" if response.status_code < 400 else "failed"
        execution_time = finish_time - start_time

        response_logging = {
            "status": overall_status,
            "status_code": response.status_code,
            "headers": response.headers,
            "time_taken": f"{execution_time:0.4f}s"
        }

        resp_body = [section async for section in response.__dict__["body_iterator"]]
        response.__setattr__("body_iterator", AsyncIteratorWrapper(resp_body))

        try:
            resp_body = json.loads(resp_body[0].decode())
        except BaseException:
            resp_body = str(resp_body)

        response_logging["body"] = resp_body

        return response, response_logging

    async def _execute_request(self, call_next: Callable, request: Request, request_id: str) -> Response:
        """
        Overview:
            Executes the actual path function using call_next; it also injects "X-API-Request-ID" header to the response
        Arguments:
            - call_next: Callable (To execute the actual path function and get response back)
            - request: Request
            - request_id: str (uuid)
        Returns:
            - response: Response
        """
        try:
            response: Response = await call_next(request)
            response.headers["X-API-Request-ID"] = request_id
            return response
        except Exception as e:
            self._logger.exception(
                {
                    "path": request.url.path,
                    "method": request.method,
                    "reason": e
                }
            )


class AsyncIteratorWrapper:
    """
    Overview:
        Transforms a regular iterable to an asynchronous one.
    Link:
        https://www.python.org/dev/peps/pep-0492/#example-2
    """

    def __init__(self, obj):
        self._it = iter(obj)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            value = next(self._it)
        except StopIteration:
            raise StopAsyncIteration
        return value
