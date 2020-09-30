



class Inventory(object):
	def __init__(self, inventory):
		self.inventory = inventory
		self.items = list(inventory.keys())

	def confirmInventory(self, item, qty):
		if item in self.inventory.keys():
			units = self.inventory[item]
			if qty <= units:
				return True
			else:
				return int(units)
		return False

	def consume(self, item, qty):
		if item in self.inventory.keys():
			units = self.inventory[item]
			if qty <= units:
				self.inventory[item] -= qty
				return True
		return False