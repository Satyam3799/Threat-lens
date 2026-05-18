from __future__ import annotations

from dataclasses import dataclass
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET

from backend.core.config import settings


def _running_in_container() -> bool:
    return os.path.exists("/.dockerenv") or os.getenv("RUNNING_IN_DOCKER", "").lower() in {
        "1",
        "true",
        "yes",
    }


class ScannerUnavailableError(RuntimeError):
    pass


class ScannerExecutionError(RuntimeError):
    pass


@dataclass(frozen=True)
class NmapScanResult:
    open_ports: list[dict]
    raw_result: dict


def _build_version_string(service_node: ET.Element | None) -> str | None:
    if service_node is None:
        return None
    product = (service_node.attrib.get("product") or "").strip()
    version = (service_node.attrib.get("version") or "").strip()
    extrainfo = (service_node.attrib.get("extrainfo") or "").strip()
    parts = [p for p in (product, version, extrainfo) if p]
    return " ".join(parts) if parts else None


class NmapScanner:
    name = "nmap"

    def __init__(self, timeout_seconds: int | None = None) -> None:
        timeout_seconds = timeout_seconds or settings.scan_timeout_seconds
        self.timeout_seconds = timeout_seconds

    def scan(self, target: str) -> NmapScanResult:
        if shutil.which("nmap") is None:
            raise ScannerUnavailableError("Nmap is not installed or is not available on PATH.")

        command = self._build_command(target)

        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                check=False,
                shell=False,
                text=True,
                timeout=self.timeout_seconds + 15,
            )
        except subprocess.TimeoutExpired as exc:
            raise ScannerExecutionError("Nmap scan timed out.") from exc

        stderr_text = (completed.stderr or "").strip()
        stdout_text = completed.stdout or ""

        if completed.returncode not in {0, 1}:
            message = stderr_text or "Nmap scan failed."
            raise ScannerExecutionError(message)

        if not stdout_text.strip():
            return NmapScanResult(
                open_ports=[],
                raw_result=self._fallback_raw(
                    target=target,
                    command=command,
                    reason="empty_output",
                    stderr=stderr_text,
                    returncode=completed.returncode,
                ),
            )

        try:
            return self._parse_xml(stdout_text, target=target, command=command, stderr=stderr_text)
        except ET.ParseError as exc:
            return NmapScanResult(
                open_ports=[],
                raw_result=self._fallback_raw(
                    target=target,
                    command=command,
                    reason="xml_parse_error",
                    stderr=stderr_text,
                    returncode=completed.returncode,
                    parse_error=str(exc),
                ),
            )

    def _build_command(self, target: str) -> list[str]:
        host_timeout = f"{self.timeout_seconds}s"
        # TCP connect scan works without root/capabilities (required in Docker).
        connect_flag = ["-sT"] if (_running_in_container() or os.getenv("NMAP_USE_CONNECT_SCAN", "").lower() in {"1", "true", "yes"}) else []

        if settings.full_port_scan_enabled:
            base = [
                "nmap",
                *connect_flag,
                "-p-",
                "-sV",
                "--version-intensity",
                "5",
                "-T3",
                "--host-timeout",
                host_timeout,
                "-oX",
                "-",
            ]
        else:
            # Top 100 ports keeps Docker scans fast and reliable vs a full slow sweep.
            port_args = ["--top-ports", "100"] if _running_in_container() else []
            base = [
                "nmap",
                *connect_flag,
                *port_args,
                "-sV",
                "-T3",
                "--host-timeout",
                host_timeout,
                "-oX",
                "-",
            ]

        return [*base, target]

    def _fallback_raw(
        self,
        *,
        target: str,
        command: list[str],
        reason: str,
        stderr: str,
        returncode: int,
        parse_error: str | None = None,
    ) -> dict:
        return {
            "scanner": self.name,
            "hosts": [],
            "args": " ".join(command),
            "nmap_parse_fallback": True,
            "fallback_reason": reason,
            "target": target,
            "returncode": returncode,
            "stderr_excerpt": stderr[:4000],
            "parse_error": parse_error,
        }

    def _parse_xml(
        self,
        xml_output: str,
        *,
        target: str,
        command: list[str],
        stderr: str,
    ) -> NmapScanResult:
        root = ET.fromstring(xml_output)

        open_ports: list[dict] = []
        hosts: list[dict] = []

        for host in root.findall("host"):
            address_node = host.find("address")
            address = address_node.attrib.get("addr") if address_node is not None else None
            host_ports: list[dict] = []

            for port_node in host.findall("./ports/port"):
                try:
                    port_id = int(port_node.attrib.get("portid", "0"))
                except (TypeError, ValueError):
                    continue
                if port_id <= 0:
                    continue

                state_node = port_node.find("state")
                state = state_node.attrib.get("state") if state_node is not None else "unknown"
                if state != "open":
                    continue

                service_node = port_node.find("service")
                service_name = service_node.attrib.get("name") if service_node is not None else None
                product = service_node.attrib.get("product") if service_node is not None else None
                version_attr = service_node.attrib.get("version") if service_node is not None else None
                extrainfo = service_node.attrib.get("extrainfo") if service_node is not None else None
                version_combined = _build_version_string(service_node)

                port = {
                    "port": port_id,
                    "protocol": port_node.attrib.get("protocol", "tcp"),
                    "state": state,
                    "service": service_name,
                    "product": product,
                    "version": version_attr,
                    "extrainfo": extrainfo,
                    "version_fingerprint": version_combined or version_attr,
                }
                open_ports.append(port)
                host_ports.append(port)

            hosts.append({"address": address, "open_ports": host_ports})

        raw_result = {
            "scanner": self.name,
            "hosts": hosts,
            "args": root.attrib.get("args") or " ".join(command),
            "version": root.attrib.get("version"),
            "nmap_parse_fallback": False,
        }

        if not open_ports and stderr:
            raw_result["stderr_excerpt"] = stderr[:4000]

        return NmapScanResult(open_ports=open_ports, raw_result=raw_result)
