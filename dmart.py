import requests 
from bs4 import BeautifulSoup
import time
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# path to input file 
CSVFILE = "input-master-bulk.csv"
ERROR_FILE = f"Error_file {CSVFILE}"
error_file = open(ERROR_FILE,"w")

# path to chrome driver
DRIVER_PATH = '/Users/malaikasheikh/python/chromedriver'
# starting a browser 
driver = webdriver.Chrome(executable_path=DRIVER_PATH)
options = Options()
options.add_argument("--window-size=1920,1200")
options.add_argument('--disable-blink-features=AutomationControlled')
#options.add_argument('--headless')
driver = webdriver.Chrome(options=options, executable_path=DRIVER_PATH)
driver.get('https://www.dmart.in/')
time.sleep(15)

def conversion(original_unit, converted_unit, unit_price, stock_quantity):
  total_price = None
  if((original_unit == "gm") and (converted_unit == "kg" or converted_unit == "kilograms")):
    one_kg_price = 1000 * unit_price
    total_price = stock_quantity * one_kg_price

  if((original_unit == "kg" or original_unit == "kilograms") and (converted_unit == "kg" or converted_unit == "kilograms")):
    total_price = stock_quantity * unit_price

  if((original_unit == "kg" or original_unit == "kilograms") and (converted_unit == "g" or converted_unit == "grams")):
    one_g_price = 0.001 * unit_price
    total_price = stock_quantity * one_g_price
  
  if((original_unit == "gm") and (converted_unit == "g" or converted_unit == "grams")):
    total_price = stock_quantity * unit_price
  
  if((original_unit == "ml") and converted_unit == "ml"):
    total_price = stock_quantity * unit_price

  if((original_unit == "ml") and (converted_unit == "litres" or converted_unit == "litre" or converted_unit == "liter")):
    one_l_price = 1000 * unit_price
    total_price = stock_quantity * one_l_price
  
  if((original_unit == "litres" or original_unit == "litre" or original_unit == "liter" or original_unit == "l") and (converted_unit == "ml")):
    one_ml_price = 0.001 * unit_price
    total_price = stock_quantity * one_ml_price

  if((original_unit == "litres" or original_unit == "litre" or original_unit == "liter" or original_unit == "l") and (converted_unit == "litres" or converted_unit == "litre" or converted_unit == "liter" or original_unit == "l")):
    total_price = stock_quantity * unit_price
  return total_price


def make_request(url):
  try:
    ppo = None
    driver.get(url)
    time.sleep(15)
    soup = BeautifulSoup(driver.page_source, 'lxml') #convert the result into lxml
    products = soup.find_all("div", class_="MuiGrid-root MuiGrid-item MuiGrid-grid-xs-12 MuiGrid-grid-sm-6 MuiGrid-grid-md-4 MuiGrid-grid-lg-auto MuiGrid-grid-xl-auto")
    if(len(products) == 0):
      return ppo
    else:
      for p in products:
        div = p.find("div", class_="src-client-components-form-elements-bootstrap-select-__bootstrap-select-module___option")
        span_tags = div.find_all("span")
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
    df.insert(9,"price", '')
    product_list = df['ingredient'] # read a column with name 'Item Name' form df
    for i in range(0, len(product_list)): # loop through all items
      print(product_list[i])
      try:
        product_name = product_list[i].lower().replace(" ","%20") #replace spaces in item name with '%20' so that we could use in url
        url = f"https://www.dmart.in/searchResult?searchTerm={product_name}" # url for each item name
        ppo = make_request(url)
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
          print(unit_price)
          print(original_unit)
          df['original unit'][i] = original_unit
          converted_unit = df['unit'][i].strip().lower()
          stock_quantity = df['Estimated Total Qty'][i]
          total_price = conversion(original_unit, converted_unit, unit_price, stock_quantity)
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