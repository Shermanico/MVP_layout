"""
Adaptadores de salida (Secondary Adapters).
"""
from adapters.output.persistence import JsonPOIRepository
from adapters.output.simulation import FakeDroneAdapter
from adapters.output.http import TelemetryServer

__all__ = ["JsonPOIRepository", "FakeDroneAdapter", "TelemetryServer"]

