from __future__ import annotations

import logging
import os
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import requests

TOKEN_URL = (
    "https://ercotb2c.b2clogin.com"
    "/ercotb2c.onmicrosoft.com"
    "/B2C_1_PUBAPI-ROPC-FLOW"
    "/oauth2/v2.0/token"
)
CLIENT_ID = "fec253ea-0d06-4272-a5e6-b478baeecd70"
SCOPE = f"openid {CLIENT_ID} offline_access"

CONNECT_TIMEOUT = 10
READ_TIMEOUT = 60
MAX_RETRIES = 3
BACKOFF_BASE = 2
TOKEN_REFRESH_BUFFER = 60

PROJECT_ROOT = Path(__file__).resolve().parents[2]
# Raw API pulls land in the new-schema raw-API folder.
OUT_DIR = PROJECT_ROOT / "01_data" / "1.2_raw_api"


class ERCOTAuth:
    """Obtain and cache an id_token via Azure AD B2C ROPC flow."""

    def __init__(self, username: str, password: str, logger: logging.Logger) -> None:
        self._username = username
        self._password = password
        self._log = logger
        self._token: str | None = None
        self._expires_at: float = 0.0

    def _request_token(self) -> str:
        self._log.info("Requesting new ERCOT id_token ...")
        payload = {
            "username": self._username,
            "password": self._password,
            "grant_type": "password",
            "client_id": CLIENT_ID,
            "scope": SCOPE,
            "response_type": "id_token",
        }
        resp = requests.post(
            TOKEN_URL,
            data=payload,
            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
        )
        resp.raise_for_status()

        body = resp.json()
        if "id_token" not in body:
            raise ValueError(f"No id_token in response: {body}")

        expires_in = int(body.get("expires_in", 3600))
        self._token = body["id_token"]
        self._expires_at = time.time() + expires_in - TOKEN_REFRESH_BUFFER
        self._log.info("Token acquired (expires in %ds).", expires_in)
        return self._token

    def get_valid_token(self) -> str:
        if self._token is None or time.time() >= self._expires_at:
            return self._request_token()
        return self._token

    def force_refresh(self) -> str:
        return self._request_token()


class ERCOTAPIClient:
    """Generic ERCOT public API client with retry and pagination helpers."""

    def __init__(self, auth: ERCOTAuth, subscription_key: str, logger: logging.Logger) -> None:
        self._auth = auth
        self._sub_key = subscription_key
        self._log = logger
        self._session = requests.Session()

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._auth.get_valid_token()}",
            "Ocp-Apim-Subscription-Key": self._sub_key,
            "Accept": "application/json",
        }

    def fetch_page(
        self,
        endpoint: str,
        params: dict[str, Any],
        page: int,
        size: int,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        paged_params = {**params, "page": page, "size": size}

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = self._session.get(
                    endpoint,
                    headers=self._headers(),
                    params=paged_params,
                    timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
                )

                # Token might be expired/revoked before expected expiry.
                if resp.status_code == 401 and attempt < MAX_RETRIES:
                    self._auth.force_refresh()
                    wait = BACKOFF_BASE ** attempt
                    self._log.warning(
                        "HTTP 401 on page %d (attempt %d/%d) - refreshing token and retrying in %ds ...",
                        page,
                        attempt,
                        MAX_RETRIES,
                        wait,
                    )
                    time.sleep(wait)
                    continue

                if resp.status_code in (429, 500, 502, 503, 504):
                    wait = BACKOFF_BASE ** attempt
                    self._log.warning(
                        "HTTP %s on page %d (attempt %d/%d) - retrying in %ds ...",
                        resp.status_code,
                        page,
                        attempt,
                        MAX_RETRIES,
                        wait,
                    )
                    time.sleep(wait)
                    continue

                resp.raise_for_status()
                return parse_payload(resp.json())

            except (requests.ConnectionError, requests.Timeout) as exc:
                wait = BACKOFF_BASE ** attempt
                self._log.warning(
                    "Network error on page %d (attempt %d/%d): %s - retrying in %ds ...",
                    page,
                    attempt,
                    MAX_RETRIES,
                    exc,
                    wait,
                )
                if attempt < MAX_RETRIES:
                    time.sleep(wait)
                else:
                    raise

        raise RuntimeError(f"Failed to fetch page {page} after {MAX_RETRIES} attempts.")


def parse_payload(body: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw_fields = body.get("fields", [])
    raw_rows = body.get("data", [])
    meta = body.get("_meta", {})

    field_names = [f["name"] if isinstance(f, dict) else f for f in raw_fields]
    rows = [dict(zip(field_names, row)) for row in raw_rows]
    return rows, meta


class ParquetChunkWriter:
    """Append pandas chunks to one parquet file without keeping everything in memory."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._writer: pq.ParquetWriter | None = None
        self._schema: pa.Schema | None = None
        self._columns: list[str] | None = None
        self.rows_written = 0

    def write(self, df: pd.DataFrame) -> None:
        if df.empty:
            return

        self._path.parent.mkdir(parents=True, exist_ok=True)

        if self._columns is None:
            self._columns = list(df.columns)
        aligned = df.reindex(columns=self._columns)

        if self._schema is None:
            table = pa.Table.from_pandas(aligned, preserve_index=False)
            self._schema = table.schema
            self._writer = pq.ParquetWriter(self._path, self._schema, compression="snappy")
        else:
            table = pa.Table.from_pandas(aligned, preserve_index=False, schema=self._schema)

        assert self._writer is not None
        self._writer.write_table(table)
        self.rows_written += len(aligned)

    def close(self) -> None:
        if self._writer is not None:
            self._writer.close()


def strip_z(ts: str) -> str:
    return ts.rstrip("Z")


def monthly_intervals(ts_from: str, ts_to: str) -> list[tuple[str, str]]:
    fmt = "%Y-%m-%dT%H:%M:%S"
    start = datetime.strptime(strip_z(ts_from), fmt)
    end = datetime.strptime(strip_z(ts_to), fmt)

    intervals: list[tuple[str, str]] = []
    current = start
    while current < end:
        if current.month == 12:
            next_month = current.replace(year=current.year + 1, month=1, day=1, hour=0, minute=0, second=0)
        else:
            next_month = current.replace(month=current.month + 1, day=1, hour=0, minute=0, second=0)

        chunk_end = min(next_month - timedelta(seconds=1), end)
        intervals.append((current.strftime(fmt), chunk_end.strftime(fmt)))
        current = next_month

    return intervals


def end_of_today_iso() -> str:
    return datetime.now().strftime("%Y-%m-%dT23:59:59")


def today_ymd() -> str:
    return date.today().strftime("%Y-%m-%d")


def require_env(name: str, logger: logging.Logger) -> str:
    val = os.environ.get(name, "").strip()
    if not val:
        logger.error("Required environment variable '%s' is not set.", name)
        sys.exit(1)
    return val
