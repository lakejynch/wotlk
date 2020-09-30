import json, csv, math, random, pprint, os
import matplotlib as mpl
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
from inventory_manager import Inventory
import enchanting.scraper as scraper

def getMatDF(df, mat_df_columns):
	mat_df = pd.DataFrame(index=df.index, columns=mat_df_columns)
	for index, row in mat_df.iterrows():
		mats = df.at[index,"materials"]
		for mat, qty in mats.items():
			mat_df.at[index, mat] = qty
	return mat_df

def getAHPrices():
	path = os.path.abspath(os.path.dirname(__name__))
	path = os.path.join(path,"enchanting","processed","auction_house.csv")
	df = pd.read_csv(path)
	df.set_index("Item", inplace=True)
	return df

def levelChance(skill, gray, yellow):
	pLevel = (gray - skill) / (gray - yellow)
	return pLevel

def lesserToGreater(lesser_price):
	return lesser_price * 3

def greaterToLesser(greater_price):
	return greater_price / 3

def exportLog(log, cost):
	pass

def analyzePath(self, results, mats_used):
	print("COMPLETED TRAINING !!! =======================")
	print("Used the following:")
	pprint.pprint(mats_used)
	print("Crafted {} items".format(results["events"]))
	print("Spent {} gold".format(results["cost"]))



class Enchanter(object):
	def __init__(self, df, mat_df, my_mats, skill_interval=3, max_skill=450):
		self.df = df
		self.mats = mat_df
		self.skill_interval = skill_interval
		self.my_mats = my_mats
		self.prices = self.cachePrices()
		self.df["cost"] = self.priceItems()
		self.skill = 1
		self.max_skill = max_skill
		self.mats_used = {}
		self.receipt = []
		self.log = []
		self.inventory = Inventory(my_mats)
		self.unlockSkills()
		print(self.df)

	def cachePrices(self):
		path = os.path.abspath(os.path.dirname(__name__))
		path = os.path.join(path,"enchanting","processed","mat_list.csv")
		prices = pd.read_csv(path)
		prices.set_index("name", inplace=True)
		ah_data = getAHPrices()
		price_series = []
		for index, row in prices.iterrows():
			price = ah_data.at[index, "BO Median"]
			if price == '':
				price_series.append(np.nan)
			else:
				price_series.append(float(price))
		prices["price"] = price_series
		return prices

	def priceItems(self):
		costs = []
		for index, row in self.df.iterrows():
			cost = self.getItemCost(index)
			costs.append(cost)
		return costs

	def getItemCost(self, item):
		mats = self.df.at[item, "materials"]
		cost = 0
		for mat, qty in mats.items():
			price = self.prices.at[mat, "price"]
			if "Lesser" in mat:
				alt = "Greater" + mat[len("Lesser"):]
				price1 = greaterToLesser(self.prices.at[alt, "price"])
				price = min(price, price1)
			elif "Greater" in mat:
				alt = "Lesser" + mat[len("Greater"):]
				price1 = lesserToGreater(self.prices.at[alt, "price"])
				price = min(price, price1)
			cost += (price * qty)
		return cost

	def unlockSkills(self):
		self.available = self.df.loc[self.df["orange"] <= self.skill].copy(deep=False)
		return self.available

	def optimizePath(self, based_on="cost"):
		if based_on == "cost":
			while self.skill < self.max_skill:
				op_costs = []
				items = []
				for index, row in self.available.iterrows():
					if self.skill >= row["gray"]:
						pass
					elif row["gray"] > 0:
						if not math.isnan(row["cost"]):
							try:
								oc = self.calculateOpCost(row["cost"],row["gray"],row["yellow"])
								op_costs.append(oc)
								items.append(index)
							except:
								print("Failed to calc cost of {}".format(index))
								print("YELLOW:",row["yellow"],"|GRAY:",row["gray"])
				ref = op_costs.index(min(op_costs))
				item = items[ref]
				self.craft(item)
		results = {"events":len(self.log), "cost":sum(self.receipt)}
		return results

	def calculateOpCost(self, cost, gray, yellow):
		prob = levelChance(self.skill, gray, yellow)
		if prob != 0:
			return (1 / prob) * cost
		else:
			return 100000000

	def craft(self, item):
		print("Crafting {}...".format(item))
		init_skill = self.skill
		if self.skill < self.df.at[item, "orange"]:
			return False
		elif self.skill < self.df.at[item, "yellow"]:
			pLevel = 1
		elif self.skill < self.df.at[item, "gray"]:
			pLevel = levelChance(self.skill, self.df.at[item, "gray"], self.df.at[item, "yellow"])
		else:
			pLevel = 0
		outcome = self.attemptLevel(item, pLevel)
		if outcome:
			print("Success! Enchanting skill leveled to {}".format(self.skill))
		else:
			print("Oops, failed to level from {}!".format(self.skill))
		mats = self.df.at[item, "materials"]
		for mat, qty in mats.items():
			price = self.consumeMaterial(mat, qty)
			self.receipt.append(qty * price)
		record = [item, init_skill, self.skill, self.skill - init_skill]
		self.log.append(record)

	def consumeMaterial(self, mat, qty):
		price = self.prices.at[mat, "price"]
		if mat in self.inventory.items:
			confirmation = self.inventory.confirmInventory(mat, qty)
			if isinstance(confirmation, int):
				attempt = self.inventory.consume(mat, confirmation)
				if attempt:
					remainder = qty - confirmation
					price = (0 * confirmation + price * remainder) / qty
			elif confirmation:
				attempt = self.inventory.consume(mat, qty)
				if attempt:
					price = 0

		if mat in self.mats_used.keys():
			self.mats_used[mat]["qty"] += qty
			self.mats_used[mat]["cost"] = self.mats_used[mat]["qty"] * price
		else:
			self.mats_used[mat] = {"qty": qty, "cost": qty * price}
		return price

	def attemptLevel(self, item, pLevel):
		S = pLevel * 100
		F = (1 - pLevel) * 100
		outcomes = [True] * int(S) + [False] * int(F)
		random.shuffle(outcomes)
		outcome = random.choice(outcomes)
		if outcome:
			self.skill += self.skill_interval
			self.unlockSkills()
			return True
		else:
			return False

def performTest(df, mat_df, loops):
	plt.figure(figsize=(12,12), dpi=100)
	i = 1
	events = []
	costs = []
	while i <= loops:
		print(">>>>>>>>> Loop #",i)
		profession = Enchanter(df, mat_df, {})
		results = profession.optimizePath()
		events.append(results["events"])
		costs.append(results["cost"])
		i += 1
	plt.scatter(x=events, y=costs, marker="o", alpha=0.8)
	plt.show()


def go(optimize=False):
	df, mat_df_columns = scraper.scrape()
	mat_df = getMatDF(df, mat_df_columns)
	print("++++++++++++++++++++++++++++++++")
	if optimize:
		performTest(df, mat_df, 100)
	else:
		profession = Enchanter(df=df, mat_df=mat_df, my_mats={})
		#results = profession.optimizePath()
		#analyzePath(results, profession.mats_used)

if __name__ == "__main__":

	go(optimize=False)
	
	
	

	

	
	
	
	

	


