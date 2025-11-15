"""
Mapper para convertir entre entidades de telemetría y DTOs.
"""
from domain.entities.telemetry import Telemetry
from app.dtos import TelemetryDTO


class TelemetryMapper:
    """Mapper para telemetría."""
    
    @staticmethod
    def to_dto(telemetry: Telemetry) -> TelemetryDTO:
        """Convierte una entidad Telemetry a TelemetryDTO."""
        return TelemetryDTO(
            drone_id=telemetry.drone_id,
            latitude=telemetry.latitude,
            longitude=telemetry.longitude,
            altitude=telemetry.altitude,
            heading=telemetry.heading,
            velocity=telemetry.velocity,
            battery=telemetry.battery,
            status=telemetry.status,
            timestamp=telemetry.timestamp,
            vertical_speed=telemetry.vertical_speed,
            rtk_fix=telemetry.rtk_fix,
            max_speed=telemetry.max_speed,
            max_altitude=telemetry.max_altitude,
            flight_time_remaining=telemetry.flight_time_remaining,
        )
    
    @staticmethod
    def to_entity(dto: TelemetryDTO) -> Telemetry:
        """Convierte un TelemetryDTO a entidad Telemetry."""
        return Telemetry(
            drone_id=dto.drone_id,
            latitude=dto.latitude,
            longitude=dto.longitude,
            altitude=dto.altitude,
            heading=dto.heading,
            velocity=dto.velocity,
            battery=dto.battery,
            status=dto.status,
            timestamp=dto.timestamp,
            vertical_speed=dto.vertical_speed,
            rtk_fix=dto.rtk_fix,
            max_speed=dto.max_speed,
            max_altitude=dto.max_altitude,
            flight_time_remaining=dto.flight_time_remaining,
        )
    
    @staticmethod
    def dict_to_entity(data: dict) -> Telemetry:
        """Convierte un diccionario a entidad Telemetry."""
        return Telemetry.from_dict(data)

