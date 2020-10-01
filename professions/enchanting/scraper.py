import json, csv, math, random, pprint, os
import pandas as pd
import numpy as np

def getDataSets():
	files = ["scraped_data/classic_enchanting.txt","scraped_data/bc_enchanting.txt","scraped_data/lk_enchanting.txt"]
	data = {}
	path = os.path.abspath(os.path.dirname(__name__))
	data["classic"] = pd.read_csv(os.path.join(path,"enchanting",files[0]), delimiter=" / ",names=["item","category","materials","skill","style","source"], quotechar='"')
	data["bc"] = pd.read_csv(os.path.join(path,"enchanting",files[1]), delimiter=" / ",names=["item","category","materials","skill","style","source"], quotechar='"')
	data["lk"] = pd.read_csv(os.path.join(path,"enchanting",files[2]), delimiter=" / ",names=["item","category","materials","skill","style","source"], quotechar='"')
	return data

def cleanDataSet(df, set_name):
	mat_list = []
	data_dict = {"item":[],"materials":[],"orange":[],"yellow":[],"green":[],"gray":[],"source":[]}
	for index, row in df.iterrows():
		
		data_dict["source"].append(formatSource(row["source"]))
		
		data_dict["item"].append(formatItem(row["item"]))
		
		mats, mat_list = formatMats(row["materials"], mat_list)
		data_dict["materials"].append(mats)

		diff = formatDiff(row["skill"], set_name)
		base = diff["orange"]
		for key in ["orange","yellow","green","gray"]:
			if key in diff.keys():
				data_dict[key].append(diff[key])
	return data_dict, mat_list

def formatDiff(diff, set_name):
	ref_dict = {"yellow":10,"green":17,"gray":25}
	diff = diff[len("RecipeTable/Difficulty|" )+1:]
	diff = diff[:-1]
	diff = diff.split("|")
	i = 0
	skill = {}
	for key in ["orange","yellow","green","gray"]:
		if diff[i] == '':
			skill[key] = np.nan
		else:
			skill[key] = int(diff[i])
		i += 1
	if set_name in ["bc","lk"]:
		if set_name == "bc":
			base = 300
		elif set_name == "lk":
			base = 375
		orange = skill["orange"] + base
		for key, value in skill.items():
			if math.isnan(skill[key]):
				skill[key] = orange + ref_dict[key]
			else:
				skill[key] = value + base
	return skill

def formatItem(item):
	item = item[1:]
	item = item[:-1]
	return item

def formatSource(source):
	if "Formula" in source:
		return "Formula"
	else:
		return "Trainer"

def formatMats(mats, mat_list):
	mat_dict = {}
	if "," in mats:
		mats = mats.split(",")
		for mat in mats:
			qty, name = mat.split("x ")
			name = name[1:]
			name = name[:-1]
			mat_dict[name] = int(qty)
	else:
		qty, name = mats.split("x ")
		name = name[1:]
		name = name[:-1]
		mat_dict[name] = int(qty)
	for key in mat_dict.keys():
		if key not in mat_list:
			mat_list.append(key)
	return mat_dict, mat_list

def scrape():
	datasets = getDataSets()
	data_dict = {"item":[],"materials":[],"orange":[],"yellow":[],"green":[],"gray":[],"source":[]}
	mat_df_columns = []
	for key, df in datasets.items():
		datasets[key], mat_list = cleanDataSet(df, key)
		for mat in mat_list:
			if mat not in mat_df_columns:
				mat_df_columns.append(mat)
		for col, series in datasets[key].items():
			data_dict[col] += datasets[key][col]
	df = pd.DataFrame.from_dict(data_dict, orient="columns")
	df.set_index("item", inplace=True)
	return df, mat_df_columns

if __name__ == "__main__":
	df, mat_df_columns = scrape()
	print(df)