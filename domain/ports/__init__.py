"""
Puertos (Ports) - Interfaces del dominio.
"""
from domain.ports.input import IDroneService, IPOIService
from domain.ports.output import IDroneRepository, IPOIRepository, ITelemetryRepository

__all__ = [
    "IDroneService", "IPOIService",
    "IDroneRepository", "IPOIRepository", "ITelemetryRepository"
]

