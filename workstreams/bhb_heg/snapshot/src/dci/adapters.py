"""Public read-only Solana RPC. No transaction submission or credentials."""
import json
from typing import Protocol
from urllib.request import Request, urlopen

from .models import Buy, RiskEvidence


class SolanaSource(Protocol):
    def signatures(self, address: str, before: str | None = None) -> list[dict]: ...
    def transaction(self, signature: str) -> dict | None: ...


class BuyerDiscovery(Protocol):
    def early_buyers(self, token: str, launch: int, cutoff: int) -> list[Buy]: ...


class RiskSource(Protocol):
    def risk(self, token: str, as_of: int) -> RiskEvidence: ...


class RpcError(RuntimeError):
    pass


class PublicSolanaRpc:
    # Endpoint is deliberately fixed: arbitrary URLs and secret-bearing providers
    # require a separately reviewed adapter, not runtime credential discovery.
    endpoint = "https://api.mainnet-beta.solana.com"
    methods = frozenset({"getSlot", "getSignaturesForAddress", "getTransaction", "getAccountInfo"})

    def __init__(self, transport=None):
        self.transport = transport or self._http

    def _http(self, payload: dict) -> dict:
        request = Request(self.endpoint, data=json.dumps(payload).encode(),
                          headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=10) as response:
            data = response.read(4_000_001)
        if len(data) > 4_000_000:
            raise RpcError("response too large")
        return json.loads(data)

    def call(self, method: str, params: list):
        if method not in self.methods:
            raise RpcError("method is outside read-only allowlist")
        try:
            response = self.transport({"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
            if not isinstance(response, dict) or response.get("id") != 1 or response.get("jsonrpc") != "2.0" or "error" in response or "result" not in response:
                raise RpcError("invalid or failed RPC response")
            return response["result"]
        except (OSError, ValueError) as exc:
            raise RpcError("RPC unavailable or malformed") from exc

    def signatures(self, address: str, before: str | None = None) -> list[dict]:
        options = {"commitment": "finalized", "limit": 100}
        if before:
            options["before"] = before
        result = self.call("getSignaturesForAddress", [address, options])
        if not isinstance(result, list):
            raise RpcError("invalid signature result")
        return result

    def transaction(self, signature: str) -> dict | None:
        result = self.call("getTransaction", [signature, {"commitment": "finalized", "encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}])
        if result is not None and not isinstance(result, dict):
            raise RpcError("invalid transaction result")
        return result

    def account(self, address: str) -> dict:
        result = self.call("getAccountInfo", [address, {"commitment": "finalized", "encoding": "jsonParsed"}])
        if not isinstance(result, dict):
            raise RpcError("invalid account result")
        return result
