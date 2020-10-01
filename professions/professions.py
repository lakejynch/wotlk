import random
import pandas as pd


class Profession(object):

	'''
	General util class for professions designed for specific-profession class inheritance;
	Specific profession classes must have:
		> Event Log (self.log)
		> Expense Log (self.receipt)
		> Resource Log (self.mats_used)
		> Price Dataframe where cols=[Item, Price] (self.prices)
		> Inventory class (self.inventory)
	'''
	def levelSkill(self, skill):
		''' Return skill if not maxed '''
		if skill + self.skill_interval > self.max_skill:
			return skill
		else:
			return skill + self.skill_interval

	def unlockSkills(self, skill, formulas):
		''' Return available skills based on current skill level '''
		available = formulas.loc[formulas["orange"] <= skill].copy(deep=False)
		return available

	def getOpportunityCost(self, skill, gray_skill, yellow_skill):
		''' Return opportunity cost of leveling a skill, calculated: P(Level) x Cost of Mats '''
		prob = self.getLevelProbability(skill, gray_skill, yellow_skill)
		if prob != 0:
			return (1 / prob) * cost
		# if probability == 0 (e.g. skill > gray skill, return max cost)
		else:
			return 1000000000000

	def getLevelProbability(self, skill, gray_skill, yellow_skill):
		''' Return probability of leveling based on current skill, skill level for gray and skill level for yellow '''
		if skill >= gray_skill:
			return 0
		return (gray_skill - skill) / (gray_skill - yellow_skill)

	def craft(self, skill, item, formulas):
		''' Attempt to craft an item, if not possible (e.g. orange > skill), return False
			else,  '''
		print("Crafting {}...".format(item))
		init_skill = skill
		# if crafter cannot craft item
		if skill < formulas.at[item, "orange"]:
			return False
		# if orange > skill > yellow, P(level) = 1.0
		elif skill < formulas.at[item, "yellow"]:
			pLevel = 1
		# if yellow <= skill < gray, call func to calculate P(level)
		elif skill < formulas.at[item, "gray"]:
			pLevel = self.getLevelProbability(skill, formulas.at[item, "gray"], formulas.at[item, "yellow"])
		# if skill < gray, P(level) = 0
		else:
			pLevel = 0
		# identify materials from formula dataframe to consume
		mats = formulas.at[item, "materials"]
		for mat, qty in mats.items():
			# consume materials, return price
			price = self.consumeMaterial(mat, qty)
			# cache cost of mats
			self.receipt.append(qty * price)
		# cache event
		self.log.append([item, init_skill, skill, skill - init_skill])
		# attempt to level
		outcome = self.attemptLevel(pLevel)
		# if successful, print statement
		if outcome:
			print("Success! Enchanting skill leveled to {}".format(skill))
			return True
		# if failed, print statement
		else:
			print("Oops, failed to level from {}!".format(skill))
			return False
		

	def attemptLevel(self, pLevel):
		''' Return true if level attempt is successful, else False '''
		rand_var = random.random()
		if rand_var <= plevel:
			return True
		return False
		
	def consumeMaterial(self, mat, qty):
		'''
		Consume a material + qty, attempt to draw from inventory first (via Inventory.confirmInventory()).
		If successful, deplete inventory relative to qty;
		If not available, price based on available inventory (where price=0) and AH Buyout prices.
		'''
		# cache AH buyout price
		price = self.prices.at[mat, "price"]
		# check inventory
		if mat in self.inventory.items:
			# confirm qty
			confirmation = self.inventory.confirmInventory(mat, qty)
			# if confirmation is an integer value 'X', 'X' qty is available from mats, remaining must be bought
			if isinstance(confirmation, int):
				# consume available
				attempt = self.inventory.consume(mat, confirmation)
				# if successfully consumed, calculate price based on avg cost basis of inventory + AH
				if attempt:
					remainder = qty - confirmation
					price = (0 * confirmation + price * remainder) / qty
			# if confirmation = True, mats are available in inventory, price = 0
			elif confirmation:
				attempt = self.inventory.consume(mat, qty)
				if attempt:
					price = 0
		# record mats used in process
		if mat in self.mats_used.keys():
			self.mats_used[mat]["qty"] += qty
			self.mats_used[mat]["cost"] = self.mats_used[mat]["qty"] * price
		else:
			self.mats_used[mat] = {"qty": qty, "cost": qty * price}
		# return cost basis for unit of mats
		return price