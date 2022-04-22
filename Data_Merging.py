#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 31 10:39:02 2022

@author: Broth
"""
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

#define today
today = datetime.today().strftime('%Y-%m-%d')

#read in df
lines_final = pd.read_csv('./Data/lines_' + str(today) + '.csv')
torv_df = pd.read_csv('./Data/torvick_' + str(today) + '.csv')
hasla_df = pd.read_csv('./Data/hasla_' + str(today) + '.csv')
mapping_home = pd.read_csv('./Data/CBB_Matching.csv')
mapping_away = pd.read_csv('./Data/CBB_Matching.csv')

#define home/mappings
mapping_home.columns = [column + '_home' for column in mapping_home.columns]
mapping_away.columns = [column + '_away' for column in mapping_away.columns]

##cleaning values

#basketball api
ncaab = pysbr.NCAAB()

#create lookup table that matches team id to name
teams_lookup = pd.DataFrame(ncaab.league_config()['teams'])

teams_lookup['full name'] = teams_lookup.name + ' '  + teams_lookup.nickname

#remove nicknames from home and away teams
lines_final = pd.merge(lines_final, teams_lookup, left_on = 'Home Team', right_on = 'full name')
lines_final['Home Team'] = lines_final.apply(lambda x: x['Home Team'].replace(str(x['nickname']), '').strip(), axis=1)
lines_final = lines_final[[column for column in lines_final.columns if column not in teams_lookup.columns]]

lines_final = pd.merge(lines_final, teams_lookup, left_on = 'Away Team', right_on = 'full name')
lines_final['Away Team'] = lines_final.apply(lambda x: x['Away Team'].replace(str(x['nickname']), '').strip(), axis=1)
lines_final = lines_final[[column for column in lines_final.columns if column not in teams_lookup.columns]]



#add merge column
lines_final = pd.merge(lines_final,
                       mapping_home[['PySBR_home', 'Hasla_home', 'Bartorvik_home']],
                       left_on= 'Home Team',
                       right_on = 'PySBR_home',
                       how = 'left')
lines_final = pd.merge(lines_final,
                       mapping_away[['PySBR_away', 'Hasla_away', 'Bartorvik_away']],
                       left_on= 'Away Team',
                       right_on = 'PySBR_away',
                       how = 'left')


final_df = pd.merge(lines_final,
                    hasla_df,
                    left_on = ['Hasla_home', 'Hasla_away'],
                    right_on = ['Home', 'Away'])
final_df = pd.merge(final_df,
                    torv_df,
                    left_on = ['Bartorvik_home', 'Bartorvik_away'],
                    right_on = ['Home', 'Away'])


final_df.columns






