import json, csv, math, random, pprint, os
import matplotlib as mpl
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
from inventory_manager import Inventory
import enchanting.scraper as scraper
from professions import Profession

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

def exportLog(log, cost):
	pass

def analyzePath(self, results, mats_used):
	print("COMPLETED TRAINING !!! =======================")
	print("Used the following:")
	pprint.pprint(mats_used)
	print("Crafted {} items".format(results["events"]))
	print("Spent {} gold".format(results["cost"]))



class Enchanter(Profession):
	def __init__(self, df, mat_df, my_mats, skill_interval=3, max_skill=450):
		# General objects
		self.skill_interval = skill_interval
		self.skill = 1
		self.max_skill = max_skill

		# Profession-class objects
		self.mats_used = {}
		self.receipt = []
		self.log = []
		self.inventory = Inventory(my_mats)
		self.prices = self.cachePrices()

		# Profession-specific objects
		self.formulas = df
		self.formulas["cost"] = self.priceItems()
		self.mats = mat_df
		self.my_mats = my_mats

		# Init function
		self.available = self.unlockSkills(self.skill, self.formulas)

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
		for index, row in self.formulas.iterrows():
			cost = self.getItemCost(index)
			costs.append(cost)
		return costs

	def getItemCost(self, item):
		mats = self.formulas.at[item, "materials"]
		cost = 0
		for mat, qty in mats.items():
			price = self.prices.at[mat, "price"]
			if "Lesser" in mat:
				alt = "Greater" + mat[len("Lesser"):]
				price1 = self.greaterToLesser(self.prices.at[alt, "price"])
				price = min(price, price1)
			elif "Greater" in mat:
				alt = "Lesser" + mat[len("Greater"):]
				price1 = self.lesserToGreater(self.prices.at[alt, "price"])
				price = min(price, price1)
			cost += (price * qty)
		return cost

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
								oc = self.getOpportunityCost(row["cost"],row["gray"],row["yellow"])
								op_costs.append(oc)
								items.append(index)
							except:
								print("Failed to calc cost of {}".format(index))
								print("YELLOW:",row["yellow"],"|GRAY:",row["gray"])
				ref = op_costs.index(min(op_costs))
				item = items[ref]
				result = self.craft(self.skill, item, self.formulas)
				if result:
					self.skill = self.levelSkill(self.skill)
					self.available = self.unlockSkills(self.skill, self.formulas)
		# return efficiency metrics
		return {"events":len(self.log), "cost":sum(self.receipt)}

	def lesserToGreater(self, lesser_price):
		return lesser_price * 3

	def greaterToLesser(self, greater_price):
		return greater_price / 3










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
	from ..professions import Profession
	go(optimize=False)
	
	
	

	

	
	
	
	

	


