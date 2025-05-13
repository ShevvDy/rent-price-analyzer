from pydantic import BaseModel, root_validator


class Data(BaseModel):
    totalArea: float
    isApartments: bool = False
    flatType: str # flat, studio, apartments
    floors_count: int
    floorNumber: int
    roomsCount: int
    building_material: str # old, brick, monolith, monolithBrick, panel, block, other
    elevators: int
    balconiesCount: int
    hasFurniture: bool
    address: str
    home_id: int | None = None

    @root_validator(pre=True)
    def validate_flat_type(cls, values: dict):
        # Определяем isApartments на основе flatType
        flat_type = values.get("flatType")
        if flat_type == "apartments":
            values["isApartments"] = True
        elif flat_type == "studio":
            values["isApartments"] = False
            # studio всегда должна иметь 0 комнат
            if values.get("roomsCount", 0) != 0:
                values['roomsCount'] = 0
        elif flat_type == "flat":
            values["isApartments"] = False
        elif values.get('home_id') is None:
            raise ValueError("Недопустимое значение flatType.")
        return values
