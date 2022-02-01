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

#cleaning
torv_df['Home'] = torv_df['Home'].apply(lambda x: x.replace('St.', 'State'))
torv_df['Away'] = torv_df['Away'].apply(lambda x: x.replace('St.', 'State'))

hasla_df['Home'] = hasla_df['Home'].apply(lambda x: x.replace('St.', 'State').\
                                                      replace('N.', 'North').\
                                                      replace('W.', 'West').\
                                                      replace('E.', 'East').\
                                                      replace('S.', 'South').\
                                                      replace('SIUE', 'SIU Edwardsville').\
                                                      replace('Grambling', 'Grambling State').\
                                                      strip())
    
hasla_df['Away'] = hasla_df['Away'].apply(lambda x: x.replace('St.', 'State').\
                                                      replace('N.', 'North').\
                                                      replace('W.', 'West').\
                                                      replace('E.', 'East').\
                                                      replace('S.', 'South').\
                                                      replace('SIUE', 'SIU Edwardsville'))   

#basketball api
ncaab = pysbr.NCAAB()

#create lookup table that matches team id to name
teams_lookup = pd.DataFrame(ncaab.league_config()['teams'])

teams_lookup['full name'] = teams_lookup.name + ' '  + teams_lookup.nickname

#remove nicknames from home and away teams
lines_final = pd.merge(lines_final, teams_lookup, left_on = 'Home Team', right_on = 'full name')
lines_final['Home Team'] = lines_final.apply(lambda x: x['Home Team'].replace(str(x['nickname']), ''), axis=1)
lines_final = lines_final[[column for column in lines_final.columns if column not in teams_lookup.columns]]

lines_final = pd.merge(lines_final, teams_lookup, left_on = 'Away Team', right_on = 'full name')
lines_final['Away Team'] = lines_final.apply(lambda x: x['Away Team'].replace(str(x['nickname']), ''), axis=1)
lines_final = lines_final[[column for column in lines_final.columns if column not in teams_lookup.columns]]


N = 80

#create mapping for home and away teams

home_fuzzy = {tup: fuzz.ratio(*tup) for tup in 
           product(torv_df['Home'].tolist(), lines_final['Home Team'].tolist())}
home_series = pd.Series(home_fuzzy)
home_series_trimmed = home_series[home_series > N]
home_final = home_series_trimmed[home_series_trimmed.groupby(level=0).idxmax()].reset_index()


away_fuzzy = {tup: fuzz.ratio(*tup) for tup in 
           product(torv_df['Away'].tolist(), lines_final['Away Team'].tolist())}
away_series = pd.Series(away_fuzzy)
away_series_trimmed = away_series[away_series > N]
away_final = away_series_trimmed[away_series_trimmed.groupby(level=0).idxmax()].reset_index()

home_final.columns = ['Torv Home', 'Lines Home', 'Fuzzy Home Pct']
away_final.columns = ['Torv Away', 'Lines Away', 'Fuzzy Away Pct']

home_final.sort_values(by = 'Fuzzy Home Pct', ascending = False, inplace = True)
away_final.sort_values(by = 'Fuzzy Away Pct', ascending = False, inplace = True)

#join home mappings to torv and lines df
lines_final = pd.merge(lines_final, home_final, left_on = 'Home Team', right_on = 'Lines Home')
lines_final = pd.merge(lines_final, away_final, left_on = 'Away Team', right_on = 'Lines Away')

torv_df = pd.merge(torv_df, home_final, left_on = 'Home', right_on = 'Torv Home')
torv_df = pd.merge(torv_df, away_final, left_on = 'Away', right_on = 'Torv Away')


#join torv and lines together
lines_torv_merge = pd.merge(torv_df, 
                      lines_final, 
                      left_on = ['Lines Home', 'Lines Away'],
                      right_on = ['Home Team', 'Away Team'])


#prep hasla for merging 

#home
home_fuzzy2a = {tup: fuzz.ratio(*tup) for tup in 
           product(lines_torv_merge['Home Team'].tolist(), hasla_df['Home'].tolist())}
home_series2a = pd.Series(home_fuzzy2a)
home_series_trimmed2a = home_series2a[home_series2a > N]
home_final2a = home_series_trimmed2a[home_series_trimmed2a.groupby(level=0).idxmax()].reset_index()

home_fuzzy2b = {tup: fuzz.ratio(*tup) for tup in 
           product(lines_torv_merge['Home Team'].tolist(), hasla_df['Away'].tolist())}
home_series2b = pd.Series(home_fuzzy2b)
home_series_trimmed2b = home_series2b[home_series2b > N]
home_final2b = home_series_trimmed2b[home_series_trimmed2b.groupby(level=0).idxmax()].reset_index()

home_final2 = pd.concat([home_final2a, home_final2b], axis = 0)
home_final2.columns = ['Merged Home', 'Hasla Home', 'Fuzzy Home Pct']
home_final2.sort_values(by = 'Fuzzy Home Pct', ascending = False, inplace = True)
home_final2['Merged Home'] = home_final2['Merged Home'].str.strip()

#away
away_fuzzy2a = {tup: fuzz.ratio(*tup) for tup in 
           product(lines_torv_merge['Away Team'].tolist(), hasla_df['Away'].tolist())}
away_series2a = pd.Series(away_fuzzy2a)
away_series_trimmed2a = away_series2a[away_series2a > N]
away_final2a = away_series_trimmed2a[away_series_trimmed2a.groupby(level=0).idxmax()].reset_index()

away_fuzzy2b = {tup: fuzz.ratio(*tup) for tup in 
           product(lines_torv_merge['Away Team'].tolist(), hasla_df['Home'].tolist(), )}
away_series2b = pd.Series(away_fuzzy2b)
away_series_trimmed2b = away_series2b[away_series2b > N]
away_final2b = away_series_trimmed2b[away_series_trimmed2b.groupby(level=0).idxmax()].reset_index()

away_final2 = pd.concat([away_final2a, away_final2b], axis = 0).reset_index(drop = True)
away_final2.columns = ['Merged Away', 'Hasla Away', 'Fuzzy Away Pct']
away_final2.sort_values(by = 'Fuzzy Away Pct', ascending = False, inplace = True)
away_final2['Merged Away'] = away_final2['Merged Away'].str.strip()


#join mappings to torv_lines and hasla
lines_torv_merge = pd.merge(lines_torv_merge, home_final2, left_on = 'Home', right_on = 'Merged Home', how = 'right')
lines_torv_merge = pd.merge(lines_torv_merge, away_final2, left_on = 'Away', right_on = 'Merged Away')

hasla_df = pd.merge(hasla_df, home_final2, left_on = 'Home', right_on = 'Merged Home', how  = 'left')
hasla_df = pd.merge(hasla_df, away_final2, left_on = 'Away', right_on = 'Hasla Away', how = 'left')

#hasla and torv_lines
final_df = pd.merge(lines_torv_merge, 
                    hasla_df, 
                    left_on = ['Hasla Home', 'Hasla Away'], 
                    right_on = ['Hasla Home', 'Hasla Away'])

