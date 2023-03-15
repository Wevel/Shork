import dataclasses
from typing import Any

import Ingredients
import Tools


@dataclasses.dataclass(frozen=True)
class Recipe:
	key: str
	name: str
	description: str
	isLiquid: bool
	serviceSize: Tools.Quantity
	ingredients: dict[str, Tools.Quantity]
	instructions: list[str] = dataclasses.field(default_factory=list)

	def CalculateNutrition(self, registeredIngredients: dict[str, Ingredients.Ingredient]) -> Tools.Nutrition:
		nutrition = Tools.Nutrition.Create(isLiquid=self.isLiquid)
		for key, quantity in self.ingredients.items():
			ingredient = registeredIngredients[key]
			if quantity.unit.isDimensionless:
				nutrition += ingredient.nutrition * (quantity * ingredient.unitQuantity / ingredient.nutrition.quantity)
			else:
				nutrition += ingredient.nutrition * (quantity / ingredient.nutrition.quantity)
		return nutrition

	def GetServing(self, registeredIngredients: dict[str, Ingredients.Ingredient]) -> Tools.Nutrition:
		return self.CalculateNutrition(registeredIngredients) * self.serviceSize

	@classmethod
	def FromJSON(cls, json: dict[str, Any]) -> "Recipe":
		if "instructions" in json:
			return cls(key=json["key"],
			           name=json["name"],
			           description=json["description"],
			           isLiquid=json["isLiquid"],
			           serviceSize=Tools.Quantity.Create(json["serviceSize"]),
			           ingredients={key: Tools.Quantity.Create(value) for key, value in json["ingredients"].items()},
			           instructions=json["instructions"])
		else:
			return cls(key=json["key"],
			           name=json["name"],
			           description=json["description"],
			           isLiquid=json["isLiquid"],
			           serviceSize=Tools.Quantity.Create(json["serviceSize"]),
			           ingredients={key: Tools.Quantity.Create(value) for key, value in json["ingredients"].items()})


ingredients = [Ingredients.Ingredient.FromJSON(item) for item in Tools.LoadJSON("ingredients.json")["items"]]
ingredients = {item.key: item for item in ingredients}
recipes = [Recipe.FromJSON(item) for item in Tools.LoadJSON("recipes.json")["items"]]
for item in recipes:
	print(item.name)
	item.GetServing(ingredients).Print()