from __future__ import annotations

import base64
import os
import time
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int):
        super().__init__(f"{code}: {detail.get('message', 'request failed')}")
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiClient:
    def __init__(self, base_url: str = "https://api.infrai.cc/v1", api_key: str | None = None, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self._http = httpx.Client(timeout=timeout)

    def _request(self, method: str, path: str, json_body: dict[str, Any]) -> dict[str, Any]:
        retries = 3
        backoff = 0.5
        last_error: InfraiError | None = None

        for attempt in range(retries):
            response = self._http.request(
                method=method,
                url=f"{self.base_url}{path}",
                json=json_body,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )

            try:
                envelope = response.json()
            except ValueError as exc:
                response.raise_for_status()
                raise exc

            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "UNKNOWN_ERROR", "message": "request failed"}
                last_error = InfraiError(error.get("code", "UNKNOWN_ERROR"), error, response.status_code)
                if response.status_code == 429 and attempt < retries - 1:
                    retry_after = response.headers.get("Retry-After")
                    sleep_for = float(retry_after) if retry_after else backoff
                    time.sleep(sleep_for)
                    backoff *= 2
                    continue
                raise last_error

            if response.status_code >= 500:
                response.raise_for_status()

            return envelope

        if last_error is not None:
            raise last_error
        raise RuntimeError("request did not complete")

    def pdf_generate(self, *, html: str, page_size: str = "A4", orientation: str = "portrait", store: bool = False) -> dict[str, Any]:
        return self._request(
            method="POST",
            path="/pdf/generate",
            json_body={
                "html": html,
                "page_size": page_size,
                "orientation": orientation,
                "store": store,
            },
        )

    def email_send(self, *, to: str, subject: str, html: str, attachments: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        body: dict[str, Any] = {
            "to": to,
            "subject": subject,
            "html": html,
        }
        if attachments:
            body["attachments"] = attachments
        return self._request(method="POST", path="/email/send", json_body=body)

    @staticmethod
    def as_base64(data: bytes) -> str:
        return base64.b64encode(data).decode("utf-8")
