import os
import json
import dataclasses
import functools
import re
from typing import Union, ClassVar


@dataclasses.dataclass(frozen=True, eq=True)
class Unit:
	powers: dict[str, int] = dataclasses.field(hash=False)

	@functools.cached_property
	def unitString(self) -> str:
		positivePowerKeys = sorted([key for key in self.powers.keys() if self.powers[key] > 0])
		negativePowerKeys = sorted([key for key in self.powers.keys() if self.powers[key] < 0])
		positivePowers = "".join([key if self.powers[key] == 1 else f"{key}^{self.powers[key]}" for key in positivePowerKeys]) if len(positivePowerKeys) > 0 else "1"
		negativePowers = "".join([key if self.powers[key] == -1 else f"{key}^{abs(self.powers[key])}" for key in negativePowerKeys])

		return f"{positivePowers}/{negativePowers}" if negativePowers else positivePowers

	@property
	def isDimensionless(self) -> bool:
		return len([value for value in self.powers.values() if value != 0]) == 0

	def __str__(self) -> str:
		return self.unitString

	def __repr__(self) -> str:
		return f"Unit({self})"

	def __hash__(self) -> int:
		return hash(self.unitString)

	def __mul__(self, other: "Unit") -> "Unit":
		return Unit({key: self.powers.get(key, 0) + other.powers.get(key, 0) for key in set(self.powers.keys()) | set(other.powers.keys()) if self.powers.get(key, 0) + other.powers.get(key, 0) != 0})

	def __truediv__(self, other: "Unit") -> "Unit":
		return Unit({key: self.powers.get(key, 0) - other.powers.get(key, 0) for key in set(self.powers.keys()) | set(other.powers.keys()) if self.powers.get(key, 0) - other.powers.get(key, 0) != 0})

	def __pow__(self, power: int) -> "Unit":
		return Unit({key: value * power for key, value in self.powers.items()})

	@classmethod
	def Create(cls, value: str) -> "Unit":
		parts = value.split("/")
		if len(parts) == 1:
			return cls({parts[0]: 1})
		elif len(parts) == 2:
			if parts[0] == "1":
				return cls({parts[1]: -1})
			else:
				return cls({parts[0]: 1, parts[1]: -1})
		else:
			raise ValueError(f"Invalid unit '{value}'")


@dataclasses.dataclass(frozen=True)
class Quantity:
	_unitScales: ClassVar[dict[str, dict[str, "Quantity",]]] = {}

	value: float
	unit: Unit

	def __str__(self) -> str:
		return f"{self.value:0.3g}{self.unit}"

	def __repr__(self) -> str:
		return f"Quantity({self})"

	def __add__(self, other: "Quantity") -> "Quantity":
		if self.unit == other.unit:
			return Quantity(self.value + other.value, self.unit)
		else:
			selfUnitString = str(self.unit)
			otherUnitString = str(other.unit)
			if selfUnitString in self._unitScales and otherUnitString in self._unitScales[selfUnitString]:
				return self + (other * self._unitScales[selfUnitString][otherUnitString])
			else:
				raise ValueError(f"Cannot add quantities with different units '{self.unit}' and '{other.unit}'")

	def __mul__(self, other: Union["Quantity", float, int]) -> "Quantity":
		if type(other) is Quantity:
			return Quantity(self.value * other.value, self.unit * other.unit).Simplify()
		elif type(other) is float or type(other) is int:
			return Quantity(self.value * other, self.unit)
		else:
			raise ValueError(f"Cannot multiply quantity by '{type(other).__name__}'")

	def __truediv__(self, other: Union["Quantity", float, int]) -> "Quantity":
		if type(other) is Quantity:
			return Quantity(self.value / other.value, self.unit / other.unit).Simplify()
		elif type(other) is float or type(other) is int:
			return Quantity(self.value / other, self.unit)
		else:
			raise ValueError(f"Cannot divide quantity by '{type(other).__name__}'")

	def __pow__(self, power: int) -> "Quantity":
		return Quantity(self.value**power, self.unit**power).Simplify()

	def Simplify(self) -> "Quantity":
		if self.unit.isDimensionless:
			return self
		else:
			current = self

			def simplifyStep() -> bool:
				nonlocal current

				for unit in current.unit.powers:
					if unit in self._unitScales:
						for key, scale in self._unitScales[unit].items():
							if key in current.unit.powers:
								current = Quantity(current.value * scale.value**current.unit.powers[key], current.unit * scale.unit**current.unit.powers[key])
								return True

				return False

			while simplifyStep():
				pass

			return current

	@classmethod
	def AreValidUnits(cls, a: "Quantity", b: "Quantity") -> bool:
		return a.unit == b.unit or a.unit == '' or b.unit == '' or (str(a.unit) in cls._unitScales and str(b.unit) in cls._unitScales[str(a.unit)])

	@classmethod
	def Create(cls, value: str | float | int) -> "Quantity":
		if type(value) is float or type(value) is int:
			return cls(value, Unit({}))
		else:
			value = str(value)

			if value[0] == '<':
				value = value[1:]

			p = re.compile(r"(\d+(?:\.\d+)?)\s*(\w+|%)")
			match = p.match(value)
			if match is None:
				raise ValueError(f"Invalid quantity '{value}'")

			parts = match.groups()
			return cls(float(parts[0]), Unit.Create(parts[1]))

	@classmethod
	def RegisterEquivalentQuantities(cls, a: "Quantity", b: "Quantity") -> None:
		if a.unit not in cls._unitScales:
			cls._unitScales[str(a.unit)] = {}

		if b.unit not in cls._unitScales:
			cls._unitScales[str(b.unit)] = {}

		cls._unitScales[str(a.unit)][str(b.unit)] = a / b
		cls._unitScales[str(b.unit)][str(a.unit)] = b / a


Quantity.RegisterEquivalentQuantities(Quantity.Create("1mg"), Quantity.Create("1000ug"))
Quantity.RegisterEquivalentQuantities(Quantity.Create("1g"), Quantity.Create("1000mg"))
Quantity.RegisterEquivalentQuantities(Quantity.Create("1kg"), Quantity.Create("1000g"))
Quantity.RegisterEquivalentQuantities(Quantity.Create("1L"), Quantity.Create("1000ml"))
Quantity.RegisterEquivalentQuantities(Quantity.Create("1ml"), Quantity.Create("1g"))  # TODO


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
		else:
			raise ValueError(f"Cannot add nutrition with different quantity units '{self.quantity}' and '{other.quantity}'")

	def __mul__(self, other: Quantity | float | int) -> "Nutrition":
		if type(other) is Quantity:
			if not other.unit.isDimensionless:
				raise ValueError(f"Cannot multiply nutrition by quantity with unit '{other.unit}'")
			return Nutrition(self.quantity * other, {key: value * other for key, value in self.values.items()})
		elif type(other) is float or type(other) is int:
			return Nutrition(self.quantity * other, {key: value * other for key, value in self.values.items()})
		else:
			raise ValueError(f"Cannot multiply nutrition by {type(other)}")

	def __truediv__(self, other: Quantity | float | int) -> "Nutrition":
		if type(other) is Quantity:
			if not other.unit.isDimensionless:
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
	def Create(cls, values: dict[str, str | int] | None = None, isLiquid: bool = False) -> "Nutrition":
		if values is None:
			return cls(Quantity.Create("0ml" if isLiquid else "0g"), {})
		else:
			allValues = {key: Quantity.Create(value) for key, value in values.items()}
			return cls(allValues["quantity"], {key: value for key, value in allValues.items() if key != "quantity"})


def LoadJSON(filePath: str) -> dict:
	if not os.path.exists(filePath):
		raise FileNotFoundError(f"File {filePath} does not exist")

	with open(filePath, 'r') as f:
		return json.load(f)
