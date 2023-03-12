import dataclasses
from typing import Any

import Ingredients
import Tools


@dataclasses.dataclass(frozen=True)
class Recipe:
	key: str
	name: str
	description: str
	ingredients: dict[str, Tools.Quantity]
	instructions: list[str] = dataclasses.field(default_factory=list)

	def CalculateNutrition(self, registeredIngredients: dict[str, Ingredients.Ingredient]) -> Tools.Nutrition:
		nutrition = Tools.Nutrition.Create()
		for key, quantity in self.ingredients.items():
			ingredient = registeredIngredients[key]
			if quantity.unit == "":
				nutrition += ingredient.nutrition * (quantity * ingredient.unitQuantity / ingredient.nutrition.quantity)
			else:
				nutrition += ingredient.nutrition * (quantity / ingredient.nutrition.quantity)
		return nutrition

	@classmethod
	def FromJSON(cls, json: dict[str, Any]) -> "Recipe":
		if "instructions" in json:
			return cls(key=json["key"], name=json["name"], description=json["description"], ingredients={key: Tools.Quantity.Create(value) for key, value in json["ingredients"].items()}, instructions=json["instructions"])
		else:
			return cls(key=json["key"], name=json["name"], description=json["description"], ingredients={key: Tools.Quantity.Create(value) for key, value in json["ingredients"].items()})


ingredients = [Ingredients.Ingredient.FromJSON(item) for item in Tools.LoadJSON("ingredients.json")["items"]]
ingredients = {item.key: item for item in ingredients}
recipes = [Recipe.FromJSON(item) for item in Tools.LoadJSON("recipes.json")["items"]]
for item in recipes:
	(item.CalculateNutrition(ingredients) / 10).Print()