#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 26 16:11:16 2022

@author: Broth
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 26 15:14:33 2022

@author: Broth
"""
#base scraping code source: https://github.com/fattmarley/cbbscraper

#import packages
import os
import pandas as pd
import numpy as np
import pysbr
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from  itertools import product
from datetime import datetime
from datetime import timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By


#path to webdriver
driver = webdriver.Chrome(os.getcwd() + '/chromedriver 2')

#get hasla site
driver.get('https://haslametrics.com/ratings.php')

#define elements
list_category_elements = driver.find_element_by_xpath('/html/body/div/table/tbody/tr[5]/td/div[3]/div/div/table') #finds hasla table elements
home = list_category_elements.find_elements(By.CLASS_NAME,"scoreproj1")
away = list_category_elements.find_elements(By.CLASS_NAME,"scoreproj2")

#initiate lists
home_team_values2=[]
away_team_values2=[]

#home team info
for i in range(len(home)):
    home_team_values2.append(home[i].text)
    
#split up team and points
home_teams = []
home_points = []


for team_score in home_team_values2:
    try:
        #points
        home_points.append(float(team_score))
    except:
        #teams/rank
        home_teams.append(team_score)

#clean teams, split name and rank
home_teams_clean = [team for team in home_teams if team != '']
home_team_names = []
home_team_ranks = []

for team in home_teams_clean:
    names_sub = []
    for name_rank in team.split():
        try:
            #rank
            home_team_ranks.append(float(name_rank))
        except:
            #names
            names_sub.append(name_rank)
            
    #if multiple strings in name
    home_team_names.append(' '.join(names_sub))

#away team info
for i in range(len(away)):
    away_team_values2.append(away[i].text)
    
#split up team and points
away_teams = []
away_points = []

for team_score in away_team_values2:
    try:
        #points
        away_points.append(float(team_score))
    except:
        #teams/ranks
        away_teams.append(team_score)

    
#clean teams, split name and rank
away_teams_clean = [team for team in away_teams if team != '']
away_team_names = []
away_team_ranks = []

for team in away_teams_clean:
    names_sub = []
    for name_rank in team.split():
        try:
            #rank
            away_team_ranks.append(float(name_rank))
        except:
            #names
            names_sub.append(name_rank)
            
    #if multiple strings in name
    away_team_names.append(' '.join(names_sub))

hasla_df = pd.DataFrame({'Home': home_team_names,
                         'Away': away_team_names,
                         'Hasla_Home_Points': home_points,
                         'Hasla_Away_Points': away_points,
                         'Hasla_Home_Rank': home_team_ranks,
                         'Hasla_Away_Rank': away_team_ranks
                         })

#scrape barttorvik
driver.get('https://barttorvik.com/schedule.php')
torvick_category_elements = driver.find_element_by_xpath('/html/body/div/div/p[4]/table/tbody') #finds torvik table elements
torvick_tags = torvick_category_elements.find_elements(By.TAG_NAME,'a')

#extract values to list
torvick_values=[]
for i in range(len(torvick_tags )):
    torvick_values.append(torvick_tags [i].text)
    
#remove blank values 
torvick_values_clean = [val for val in torvick_values if val != '' and ',' not in val]

#divide in categories
away_torv = torvick_values_clean[::3]
home_torv = torvick_values_clean[1::3]
lines_torv = torvick_values_clean[2::3]

#break lines into favorite, line, favorite score, underdog score
favorite_torv = [line.split(' -', 1)[0] for line in lines_torv]
line_torv = [line.partition('\n')[0].split(' -', 1)[1] for line in lines_torv]
scores_torv = [line.partition('\n')[2].split(' ', 1)[0] for line in lines_torv]
fav_score_torv = [score.split('-')[0] for score in scores_torv]
dog_score_torv = [score.split('-')[1] for score in scores_torv]

#match dogs/favorites to home/away
home_scores = [fav_score_torv[i] if favorite_torv[i] == home_torv[i] else dog_score_torv[i] for i in range(len(home_torv))]
away_scores = [fav_score_torv[i] if favorite_torv[i] == away_torv[i] else dog_score_torv[i] for i in range(len(away_torv))]

#create base dataframe
torv_df = pd.DataFrame({'Home': home_torv,
                        'Away': away_torv,
                        'Torv_Home_Points': home_scores,
                        'Torv_Away_Points': away_scores,
                        'Torv_Line': line_torv})

#close driver
driver.close()

#define sportsbooks and ncaab
ncaab = pysbr.NCAAB()
sb = pysbr.Sportsbook()

#get today's games
#today = (datetime.today() - timedelta(days = 1)).strftime('%Y-%m-%d')
today = datetime.today().strftime('%Y-%m-%d')
games = pysbr.EventsByDate(ncaab.league_id, datetime.strptime(today, '%Y-%m-%d'))

#create lookup table that matches team id to name
teams_lookup = pd.DataFrame(ncaab.league_config()['teams'])

teams_lookup['full name'] = teams_lookup.name + ' '  + teams_lookup.nickname

connected = False
while not connected:
    try:
        #pull bovada lines, add team names
        bovada_lines_ou = pysbr.CurrentLines(games.ids(), 
                                          ncaab.market_ids('ou'), 
                                          sb.ids(9))
        bovada_lines_ps = pysbr.CurrentLines(games.ids(), 
                                          ncaab.market_ids('ps'), 
                                          sb.ids(9))
        
        connected = True
    except:
        pass

bovada_ou_lines_df = pd.DataFrame(bovada_lines_ou.list(games))
bovada_ou_lines_df['Away Team'] = [away.split('@')[0] for away in bovada_ou_lines_df.event.values]
bovada_ou_lines_df['Home Team'] = [home.split('@')[1] for home in bovada_ou_lines_df.event.values]
bovada_ou_lines_df = bovada_ou_lines_df.sort_values('datetime', ascending = False).\
                   drop_duplicates(subset = ['event id'])


bovada_ps_lines_df = pd.DataFrame(bovada_lines_ps.list(games))
bovada_ps_lines_df['Away Team'] = [away.split('@')[0] for away in bovada_ps_lines_df.event.values]
bovada_ps_lines_df['Home Team'] = [home.split('@')[1] for home in bovada_ps_lines_df.event.values]
bovada_ps_lines_df = bovada_ps_lines_df.dropna(subset = ['participant full name'])
bovada_ps_lines_df = bovada_ps_lines_df.sort_values('datetime', ascending = False).\
                   drop_duplicates(subset = ['event id'])

bovada_ou_sub_df = bovada_ou_lines_df[['event id', 'spread / total']]
bovada_ou_sub_df.columns = ['event id', 'total bovada']

bovada_ps_sub_df = bovada_ps_lines_df[['event id', 'participant full name', 'Away Team',
       'Home Team', 'spread / total']]
bovada_ps_sub_df.columns = ['event id', 'participant full name', 'Away Team',
       'Home Team', 'Home Spread Bet354']

bovada_final = pd.merge(left = bovada_ps_sub_df,
                        right = bovada_ou_sub_df,
                        on = 'event id')


connected = False
while not connected:
    try:
        #pull bet365 lines, add team names
        bet365_lines_ou = pysbr.CurrentLines(games.ids(), 
                                          ncaab.market_ids('ou'), 
                                          sb.ids(9))
        bet365_lines_ps = pysbr.CurrentLines(games.ids(), 
                                          ncaab.market_ids('ps'), 
                                          sb.ids(9))
        
        connected = True
    except:
        pass
    
bet365_ou_lines_df = pd.DataFrame(bet365_lines_ou.list(games))
bet365_ou_lines_df['Away Team'] = [away.split('@')[0] for away in bet365_ou_lines_df.event.values]
bet365_ou_lines_df['Home Team'] = [home.split('@')[1] for home in bet365_ou_lines_df.event.values]
bet365_ou_lines_df = bet365_ou_lines_df.sort_values('datetime', ascending = False).\
                   drop_duplicates(subset = ['event id'])


bet365_ps_lines_df = pd.DataFrame(bet365_lines_ps.list(games))
bet365_ps_lines_df['Away Team'] = [away.split('@')[0] for away in bet365_ps_lines_df.event.values]
bet365_ps_lines_df['Home Team'] = [home.split('@')[1] for home in bet365_ps_lines_df.event.values]
bet365_ps_lines_df = bet365_ps_lines_df.dropna(subset = ['participant full name'])
bet365_ps_lines_df = bet365_ps_lines_df.sort_values('datetime', ascending = False).\
                   drop_duplicates(subset = ['event id'])

bet365_ou_sub_df = bet365_ou_lines_df[['event id', 'spread / total']]
bet365_ou_sub_df.columns = ['event id', 'total bet365']

bet365_ps_sub_df = bet365_ps_lines_df[['event id', 'participant full name', 'Away Team',
       'Home Team', 'spread / total']]
bet365_ps_sub_df.columns = ['event id', 'participant full name', 'Away Team',
       'Home Team', 'Home Spread Bet354']

bet365_final = pd.merge(left = bet365_ps_sub_df,
                        right = bet365_ou_sub_df,
                        on = 'event id')

lines_final = pd.merge(left = bet365_final,
                       right = bovada_final,
                       on = ['event id', 'participant full name', 'Away Team', 'Home Team'])

#save dfs
lines_final.to_csv('./Data/lines_' + str(today) + '.csv', index = False)
torv_df.to_csv('./Data/torvick_' + str(today) + '.csv', index = False)
hasla_df.to_csv('./Data/hasla_' + str(today) + '.csv', index = False)

