import os
import json
import dataclasses
import re
from typing import Union


@dataclasses.dataclass(frozen=True)
class Quantity:
	value: float
	unit: str

	def __str__(self) -> str:
		return f"{self.value:0.3g}{self.unit}"

	def __repr__(self) -> str:
		return f"Quantity({self})"

	def __add__(self, other: "Quantity") -> "Quantity":
		if self.unit == "":
			return Quantity(self.value + other.value, other.unit)
		elif other.unit == "":
			return Quantity(self.value + other.value, self.unit)
		elif self.unit == other.unit:
			return Quantity(self.value + other.value, self.unit)
		else:
			raise ValueError(f"Cannot add quantities with different units '{self.unit}' and '{other.unit}'")

	def __mul__(self, other: Union["Quantity", float, int]) -> "Quantity":
		if type(other) is Quantity:
			return Quantity(self.value * other.value, self.unit + other.unit)
		elif type(other) is float or type(other) is int:
			return Quantity(self.value * other, self.unit)
		else:
			raise ValueError(f"Cannot multiply quantity by '{type(other).__name__}'")

	def __truediv__(self, other: Union["Quantity", float, int]) -> "Quantity":
		if type(other) is Quantity:
			return Quantity(self.value / other.value, self.unit.replace(other.unit, '', 1))
		elif type(other) is float or type(other) is int:
			return Quantity(self.value / other, self.unit)
		else:
			raise ValueError(f"Cannot divide quantity by '{type(other).__name__}'")

	@staticmethod
	def AreValidUnits(a: "Quantity", b: "Quantity") -> bool:
		return a.unit == b.unit or a.unit == '' or b.unit == ''

	@classmethod
	def Create(cls, value: str | float | int) -> "Quantity":
		if type(value) is float or type(value) is int:
			return cls(value, '')
		else:
			value = str(value)

			if value[0] == '<':
				value = value[1:]

			p = re.compile(r"(\d+(?:\.\d+)?)\s*(\w+|%)")
			match = p.match(value)
			if match is None:
				raise ValueError(f"Invalid quantity '{value}'")

			parts = match.groups()
			return cls(float(parts[0]), parts[1])


@dataclasses.dataclass(frozen=True)
class Nutrition:
	quantity: Quantity
	values: dict[str, Quantity]

	def __add__(self, other: "Nutrition") -> "Nutrition":
		values = {}
		for key, value in self.values.items():
			if key in other.values:
				values[key] = value + other.values[key]
			else:
				values[key] = value

		for key, value in other.values.items():
			if key not in self.values:
				values[key] = value

		if Quantity.AreValidUnits(self.quantity, other.quantity):
			return Nutrition(self.quantity + other.quantity, values)
		elif self.quantity.unit == "ml" and other.quantity.unit == "g":
			return Nutrition(self.quantity, values)
		elif self.quantity.unit == "g" and other.quantity.unit == "ml":
			return Nutrition(other.quantity, values)
		else:
			raise ValueError(f"Cannot add nutrition with different quantity units '{self.quantity}' and '{other.quantity}'")

	def __mul__(self, other: Quantity | float | int) -> "Nutrition":
		if type(other) is Quantity:
			if other.unit != "":
				raise ValueError(f"Cannot multiply nutrition by quantity with unit '{other.unit}'")
			return Nutrition(self.quantity * other, {key: value * other for key, value in self.values.items()})
		elif type(other) is float or type(other) is int:
			return Nutrition(self.quantity * other, {key: value * other for key, value in self.values.items()})
		else:
			raise ValueError(f"Cannot multiply nutrition by {type(other)}")

	def __truediv__(self, other: Quantity | float | int) -> "Nutrition":
		if type(other) is Quantity:
			if other.unit != "":
				raise ValueError(f"Cannot divide nutrition by quantity with unit '{other.unit}'")
			return Nutrition(self.quantity / other, {key: value / other for key, value in self.values.items()})
		elif type(other) is float or type(other) is int:
			return Nutrition(self.quantity / other, {key: value / other for key, value in self.values.items()})
		else:
			raise ValueError(f"Cannot divide nutrition by '{type(other).__name__}'")

	def Print(self) -> None:
		print(f'Quantity: {self.quantity}')
		for key, value in self.values.items():
			if key != "quantity":
				print(f'{key}: {value}')

	@classmethod
	def Create(cls, values: dict[str, str | int] | None = None) -> "Nutrition":
		if values is None:
			return cls(Quantity.Create(0), {})
		else:
			allValues = {key: Quantity.Create(value) for key, value in values.items()}
			return cls(allValues["quantity"], {key: value for key, value in allValues.items() if key != "quantity"})


def LoadJSON(filePath: str) -> dict:
	if not os.path.exists(filePath):
		raise FileNotFoundError(f"File {filePath} does not exist")

	with open(filePath, 'r') as f:
		return json.load(f)
