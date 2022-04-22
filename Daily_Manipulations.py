#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 19 09:36:16 2022

@author: Broth
"""
import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings("ignore")

#read in data, date convert to datetime, order by datetime, reset index
base_df = pd.read_csv('./Data/merged_dataframe.csv', index_col = 0)
base_df.date = pd.to_datetime(base_df.date, format = '%m/%d/%Y')
base_df = base_df.sort_values(by = 'date').reset_index(drop = True)

#drop columns that aren't used
mapping_dct = {
    'Date':'date',
    'Home':'home',
    'Visitor':'road',
    'Line':'line',
    'AVG':'lineavg',
    'SAG':'linesag',
    'SPTS':'linesagp',
    'SGM':'linesaggm',
    'DONC':'linedonc',
    'FOX':'linefox',
    'MOR':'linemoore', 
    'DOK':'linedok',
    'TALR':'linetalis',
    '7OT':'line7ot',
    'RND': 'lineround', 
    'MASS':'linemassey', 
    'TRKS':'lineteamrnks',
    'DUNK':'linedunk',
    'ESPN':'lineespn', 
    'PIR':'linepir'
 }

drops = [col for col in base_df.columns if col not in mapping_dct.values() and col[:4] == 'line'] + ['SREC', 'VSS']
base_df = base_df.drop(drops, axis = 1)

#rename torvick
base_df = base_df.rename({'Torv_Line':'linetorv'}, axis = 1)

###Function####

#separate into home and road
home_df = base_df[base_df.home == 'Duke']
road_df = base_df[base_df.road == 'Duke']

#rename columns for concats
home_df = home_df.rename(mapper = {'home':'team',
                                 'hscore':'teamscore',
                                 'road':'opponent',
                                 'rscore':'opponentscore'},
                       axis = 1)

road_df = road_df.rename(mapper = {'road':'team',
                                   'rscore':'teamscore',
                                   'home':'opponent',
                                   'hscore':'opponentscore'},
                         axis = 1)

#create flag column for home and away
road_df['Flag'] = 'Road'
home_df['Flag'] = 'Home'

#multiply lines by -1 so that it matches up with team
line_cols = [line for line in home_df.columns if line[:4] == 'line']
road_df[line_cols] = road_df[line_cols] * -1

#combine into a team dataframe
team_df = pd.concat([home_df, road_df]).\
            sort_values('date').\
            reset_index(drop = True)

### generate fields to show how teams and predictions have performed ###

#team win
team_df['Win'] = np.where(team_df.teamscore > team_df.opponentscore, 1, 0)

#final score difference
team_df['Score_Diff'] = team_df.teamscore - team_df.opponentscore

#against the sspread win
team_df['ATS_Win'] = np.where(team_df['Score_Diff'].isnull(), np.nan,
                              np.where(team_df.Score_Diff > team_df.line, 1, 0))

#create fields for prediction wins
for line in [column for column in line_cols if column != 'line']:
    line_win = line[4:] + '_Overall_Win'
    team_df[line_win] = np.where(team_df[line].isnull() | team_df['Score_Diff'].isnull(), np.nan,
                                 np.where(team_df[line] < team_df['Score_Diff'], 1, 0))
                                
##calculate rolling averages for all time, last 5 games, last 10 games, last 20 games##

#Overall
#last 5 games
team_df['ATS_Overall_Last_5_Pct'] = team_df['ATS_Win'].rolling(window=5, min_periods=1).mean()
for line in [column for column in line_cols if column != 'line']:
    team_df[line + '_Overall_Last_5_Pct'] = team_df[line[4:] + '_Win'].rolling(window=5, min_periods=1).mean()
    
#last 10 games
team_df['ATS_Overall_Last_10_Pct'] = team_df['ATS_Win'].rolling(window=10, min_periods=1).mean()
for line in [column for column in line_cols if column != 'line']:
    team_df[line + '_Overall_Last_10_Pct'] = team_df[line[4:] + '_Win'].rolling(window=10, min_periods=1).mean()
    
#last 20 games
team_df['ATS_Overall_Last_20_Pct'] = team_df['ATS_Win'].rolling(window=20, min_periods=1).mean()
for line in [column for column in line_cols if column != 'line']:
    team_df[line + '_Overall_Last_20_Pct'] = team_df[line[4:] + '_Win'].rolling(window=20, min_periods=1).mean()

#home
home_df = team_df[team_df.Flag == 'Home']

home_df['ATS_Last_5_Home_Pct'] = home_df['ATS_Win'].rolling(window=5, min_periods=1).mean()
for line in [column for column in line_cols if column != 'line']:
    home_df[line + '_Last_5_Home_Pct'] = home_df[line[4:] + '_Win'].rolling(window=5, min_periods=1).mean()
    
#last 10 games
home_df['ATS_Last_10_Home_Pct'] = home_df['ATS_Win'].rolling(window=10, min_periods=1).mean()
for line in [column for column in line_cols if column != 'line']:
    home_df[line + '_Last_10_Home_Pct'] = home_df[line[4:] + '_Win'].rolling(window=10, min_periods=1).mean()
    
#last 20 games
home_df['ATS_Last_20_Home_Pct'] = home_df['ATS_Win'].rolling(window=20, min_periods=1).mean()
for line in [column for column in line_cols if column != 'line']:
    home_df[line + '_Last_20_Home_Pct'] = home_df[line[4:] + '_Win'].rolling(window=20, min_periods=1).mean()


#road
road_df = team_df[team_df.Flag == 'Road']

road_df['ATS_Last_5_Road_Pct'] = road_df['ATS_Win'].rolling(window=5, min_periods=1).mean()
for line in [column for column in line_cols if column != 'line']:
    road_df[line + '_Last_5_Road_Pct'] = road_df[line[4:] + '_Win'].rolling(window=5, min_periods=1).mean()
    
#last 10 games
road_df['ATS_Last_10_Road_Pct'] = road_df['ATS_Win'].rolling(window=10, min_periods=1).mean()
for line in [column for column in line_cols if column != 'line']:
    road_df[line + '_Last_10_Road_Pct'] = road_df[line[4:] + '_Win'].rolling(window=10, min_periods=1).mean()
    
#last 20 games
road_df['ATS_Last_20_Road_Pct'] = road_df['ATS_Win'].rolling(window=20, min_periods=1).mean()
for line in [column for column in line_cols if column != 'line']:
    road_df[line + '_Last_20_Road_Pct'] = road_df[line[4:] + '_Win'].rolling(window=20, min_periods=1).mean()


for column in road_df.columns:
    print(column)





