import requests 
from bs4 import BeautifulSoup
import time
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# path to input file 
CSVFILE = "stock-in-list.csv"
ERROR_FILE = f"Error_file {CSVFILE}"
error_file = open(ERROR_FILE,"w")

# starting a browser
options = Options()
options.add_argument("--window-size=1920,1200")
options.add_argument('--disable-blink-features=AutomationControlled')
#options.add_argument('--headless')
driver = webdriver.Chrome(options=options) # delete the executable path as there is no need of chrome driver in latest version of selenium

def conversion(original_unit, converted_unit, unit_price, qty):
  total_price = None
  if((original_unit == "gm") and (converted_unit == "kg" or converted_unit == "kilograms")):
    one_kg_price = 1000 * unit_price
    total_price = qty * one_kg_price

  if((original_unit == "kg" or original_unit == "kilograms") and (converted_unit == "kg" or converted_unit == "kilograms")):
    total_price = qty * unit_price

  if((original_unit == "kg" or original_unit == "kilograms") and (converted_unit == "g" or converted_unit == "grams")):
    one_g_price = 0.001 * unit_price
    total_price = qty * one_g_price
  
  if((original_unit == "gm") and (converted_unit == "g" or converted_unit == "grams")):
    total_price = qty * unit_price
  
  if((original_unit == "ml") and converted_unit == "ml"):
    total_price = qty * unit_price

  if((original_unit == "ml") and (converted_unit == "litres" or converted_unit == "litre" or converted_unit == "liter")):
    one_l_price = 1000 * unit_price
    total_price = qty * one_l_price
  
  if((original_unit == "litres" or original_unit == "litre" or original_unit == "liter" or original_unit == "l") and (converted_unit == "ml")):
    one_ml_price = 0.001 * unit_price
    total_price = qty * one_ml_price

  if((original_unit == "litres" or original_unit == "litre" or original_unit == "liter" or original_unit == "l") and (converted_unit == "litres" or converted_unit == "litre" or converted_unit == "liter" or original_unit == "l")):
    total_price = qty * unit_price
  return total_price

def make_request(url):
  try:
    ppo = None
    driver.get(url)
    time.sleep(9)
    products = driver.find_elements(By.XPATH, '//*[@class="search-landing_searchMainContainer__oRDlL"]/div/div')
    print("Total Products: ", len(products))
    if(len(products) == 0):
      return ppo
    else:
      for p in products:
        div_tag = p.find_element(By.XPATH, '//div/div[4]/div/div/div/div')
        span_tags = div_tag.find_elements(By.TAG_NAME, "span")
        if(len(span_tags) == 2):
          ppo = span_tags[1]
          ppo = ppo.text.replace("₹", "")
          if("1 U" in ppo):
            continue
          else:
            break
        else:
          continue
      return ppo
  except:
    pass
  return ppo

def read_csv():
    df = pd.read_csv(CSVFILE) # read csv file and store data in a dataframe name df
    df.insert(8,"original unit", '')
    product_list = df['ingredient'] # read a column with name 'Item Name' form df
    for i in range(0, len(product_list)): # loop through all items
      print(product_list[i])
      try:
        product_name = product_list[i].lower().replace(" ","%20") #replace spaces in item name with '%20' so that we could use in url
        print(i,": ",product_list[i])
        url = f"https://www.dmart.in/search?searchTerm={product_name}" # url for each item name
        ppo = make_request(url)
        print("PPO: ", ppo)
        if(ppo == None):
          df['original unit'][i] = "None"
          error_file.write(product_list[i]+"\n")
        else:
          ppo = ppo.replace("(","")
          ppo = ppo.replace(")","")
          ppo = ppo.split("/")
          unit_price = float(ppo[0].strip())
          original_unit = ppo[1].replace("1","")
          original_unit = original_unit.strip().lower()
          print("Unit price: ",unit_price)
          print("Original Price: ", original_unit)
          df['original unit'][i] = original_unit
          converted_unit = df['unit'][i].strip().lower()
          qty = df['qty'][i]
          total_price = conversion(original_unit, converted_unit, unit_price, qty)
          print("Total Price: ",total_price)
          if(total_price == None):
            error_file.write(product_list[i]+"\n")
          else:
            df['price'][i] = round(total_price,2)
      except Exception as e:
        print(e)
        continue
    df.to_csv(f"output  {CSVFILE}", index=False) # write updated df in output csv file 

read_csv()
