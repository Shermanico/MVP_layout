"""
Puertos de salida (Output Ports).
"""
from domain.ports.output.drone_repository_port import IDroneRepository
from domain.ports.output.poi_repository_port import IPOIRepository
from domain.ports.output.telemetry_repository_port import ITelemetryRepository

__all__ = ["IDroneRepository", "IPOIRepository", "ITelemetryRepository"]

