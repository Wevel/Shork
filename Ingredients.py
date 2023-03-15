from enum import Enum
import dataclasses
from typing import Any

import Tools


class FoodGroup(Enum):
	Fruit = "fruit"
	Vegetable = "vegetable"
	Meat = "meat"
	Dairy = "dairy"
	Other = "other"


@dataclasses.dataclass(frozen=True)
class Ingredient:
	key: str
	name: str
	foodGroup: FoodGroup
	unitQuantity: Tools.Quantity
	nutrition: Tools.Nutrition

	@classmethod
	def FromJSON(cls, json: dict[str, Any]) -> "Ingredient":
		return cls(key=json["key"], name=json["name"], foodGroup=FoodGroup(json["group"]), unitQuantity=Tools.Quantity.Create(json["unitQuantity"]), nutrition=Tools.Nutrition.Create(json["variants"][0]["nutrition"]))
