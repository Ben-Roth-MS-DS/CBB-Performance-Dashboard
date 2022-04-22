#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb  4 15:56:55 2022

@author: Broth
"""
import requests
import pysbr
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
import os




#path to webdriver
driver = webdriver.Chrome(os.getcwd() + '/chromedriver 2')

#get hasla site
driver.get('https://haslametrics.com/ratings.php')

#finds hasla table elements
list_category_elements = driver.find_element_by_xpath('/html/body/div/table/tbody/tr[2]/td/div[4]/div/div/div/div[2]/table/tbody')
teams = list_category_elements.find_elements(By.CLASS_NAME,"colTeam")

teams_list = []

#home team info
for i in range(len(teams)):
    teams_list.append(teams[i].text)
    
driver.close()
    
#get barttorvik tables
url = 'https://barttorvik.com/trank.php#'
html = requests.get(url).content
torv_df_matching = pd.read_html(html, header = 0)[0].reset_index(drop = True)

#reformat dataframe
columns = torv_df_matching[torv_df_matching.index == 0].values
torv_df_matching.columns = [col for col in columns]
torv_df_matching = torv_df_matching.set_axis(torv_df_matching.columns.map('_'.join), axis=1, inplace=False)

#drop weird columns
torv_df_matching = torv_df_matching.loc[torv_df_matching.Rk != 'Rk']

#drop (A) and (H) values
torv_df_matching['Team'] = [team.split(' (H)')[0] for team in torv_df_matching.Team]
torv_df_matching['Team'] = [team.split(' (A)')[0] for team in torv_df_matching.Team]

#get pysbr teams
ncaab = pysbr.NCAAB()
teams_lookup = pd.DataFrame(ncaab.league_config()['teams'])


teams_lookup


