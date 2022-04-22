#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Mar 11 22:28:04 2022

@author: Broth
"""

import os
import pandas as pd
import requests
import io
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By

#define today
today = datetime.today()

#scrape barttorvik
driver = webdriver.Chrome(os.getcwd() + '/chromedriver 2')

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

#drop games with no lines
no_lines = [line.split(' (')[0] for line in lines_torv if '-' not in line]
lines_torv = [line for line in lines_torv if '-' in line]

home_torv = home_torv[:len(lines_torv)]
away_torv = away_torv[:len(home_torv)]



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

driver.quit()


#scrape predictiontracker
driver = webdriver.Chrome(os.getcwd() + '/chromedriver 2')

 #finds torvik table elements
driver.get('https://www.thepredictiontracker.com/predbb.html')
prediction_category_elements = driver.find_element_by_xpath('/html/body/pre[2]')

#split text into lists
prediction_text = prediction_category_elements.text.split('\n')

driver.quit()

#define function to convert values to floats in list comprehension
def convert_to_float(value):
    #replace dots with value to be replaced later
    if value == '.':
        value = 100000.0        
    
    try:
        new_value = float(value)
    except:
        new_value = value
    return(new_value)

#define function to remove duplicated strings at end of row
def trim_ends(splits):
    #separate strings and floats
    strings = [split for split in splits if isinstance(split, str)]
    floats = [split for split in splits if isinstance(split, float)]
    
    #trim strings
    trim = int(len([string for string in strings if isinstance(string, str)])/2)
    new_strings = strings[:-trim]
    
    #combine trimmed strings and floats
    new_splits = [*new_strings, *floats]
    return(new_splits)

#split string
splits1 = [[convert_to_float(field) for field in line.split(' ')] for line in prediction_text]

#remove blanks and period
splits2 = [[field for field in line if field != ''] for line in splits1]

#get header columns
headers = splits2[0][:-2]

#remove first two lists (headers and empty list)
splits3 = splits2[2:]

#remove duplicate at the end
splits4 = [trim_ends(new_splits) for new_splits in splits3]


#define function for joining consequetive strings if strings in list of teams:
def school_joiner(baseline_teams, splits_list):
    #get only school names from row
    strings_list = [school for school in splits_list if isinstance(school, str)]
    
    #pull out spreads
    spreads = [spread for spread in splits_list if isinstance(spread, float)]
    
    #initiate new list
    new_strings = []
    
    #iterate through each possible consequetive combination of strings
    i = 0
    while i + 1 <= len(strings_list):
        #define possible school names
        name1 = strings_list[i]
        
        #except name 2 or 3
        try:
            name2 = strings_list[i + 1]
        except:
            name2 = 'holder'
        
        try:
            name3 = strings_list[i + 2]
        except:
            name3 = 'holder'
        
        #add three name team 
        if name1 + ' ' + name2 + ' ' + name3 in baseline_teams and (i == 0 or len(new_strings) > 0):
            new_strings.append(name1 + ' ' + name2 + ' ' + name3)
            i = i + 1
            continue
        
        #add two name
        elif name1 + ' ' + name2 in baseline_teams and (i == 0 or len(new_strings) > 0):
            new_strings.append(name1 + ' ' + name2)
            i = i + 1
            continue
        
        #if there are already two teams (e.g. existing words are 'alabama', 'texas tech' and the last word is tech):
        elif len(new_strings) == 2:
            i = i + 1
            continue
        
        elif len(new_strings) == 1 and new_strings[0].split(' ')[len(new_strings[0].split(' ')) - 1] == name1:
            i = i + 1
            continue
        
        #if last value in the list and the length of the new strings needs another spot
        elif i <= len(strings_list) - 1 and name1 in baseline_teams:
            new_strings.append(name1)
            i = i + 1
            continue
        
        #continue
        else:
            i = i + 1
            continue
    
    new_splits = [*new_strings, *spreads] 
    
    #finish function with new list of strings
    return(new_splits)
        


#load in baseline teams
baseline_teams = pd.read_csv('./Data/merged_dataframe.csv')['home'].unique()

#run function
splits5 = [school_joiner(baseline_teams, split) for split in splits4]

#convert to dataframe
prediction_df = pd.DataFrame(splits5, columns = headers)

#replace placeholder values
prediction_df = prediction_df.replace(100000.0, None)

#load in mapping df
mapping_df = pd.read_csv('./Data/CBB_Matching.csv')

#map
prediction_df =  pd.merge(prediction_df,
                          mapping_df.rename(columns = {'Torv': 'Torv_Home'}),
                          left_on = 'Home',
                          right_on = 'NCAABB')

prediction_df =  pd.merge(prediction_df,
                          mapping_df.rename(columns = {'Torv': 'Torv_Away'}),
                          left_on = 'Visitor',
                          right_on = 'NCAABB')

#merge together
daily_merged = pd.merge(prediction_df,
                        torv_df,
                        left_on = ['Torv_Home', 'Torv_Away'],
                        right_on = ['Home', 'Away'])



#drop unecessary columns
drop_columns = ['Torv_Home', 'NCAABB_x', 'Torv_Away', 'NCAABB_y',
                'Home_y', 'Away', 'Torv_Home_Points', 'Torv_Away_Points']
daily_merged = daily_merged[[column for column in daily_merged.columns if column not in drop_columns]]

#rename home
daily_merged = daily_merged.rename({'Home_x': 'Home'}, axis = 1)

#create date column
daily_merged['Date'] = today.strftime("%m/%d/%Y")


#get most recent prediction results#


#get proper year and define link
if today.month > 10:
    season_yr = str(today.year)[2:]
else:
    season_yr = str(today.year - 1)[2:]
    

#get data from link
url = 'https://www.thepredictiontracker.com/ncaabb' + season_yr + '.csv'
headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:66.0) Gecko/20100101 Firefox/66.0"}
req = requests.get(url, headers=headers)

#convert to df
daily_txt= io.StringIO(req.text)
daily_df = pd.read_csv(daily_txt)

#read in merge_df
merged_df = pd.read_csv('./Data/merged_dataframe.csv', index_col=0)

#remove yesterday's values that don't have hscore and rscore
merged_df = merged_df.dropna(axis = 0, subset = ['hscore', 'rscore'], thresh= 1)

#filter daily_df to only include new dates
new_dates = [date for date in daily_df.date.unique() if date not in merged_df.date.values]
daily_df = daily_df.loc[daily_df.date.isin(new_dates), ]


#add torvick predictions
torv_final = None
for date in [date for date in new_dates]:
    
    month = date.split('/')[0]
    day = date.split('/')[1]
    year = date.split('/')[2]
    
    web_date = year + month + day
    
    #scrape barttorvik
    driver = webdriver.Chrome(os.getcwd() + '/chromedriver 2')

    driver.get('https://barttorvik.com/schedule.php?date=' + web_date + '&conlimit=')
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

    #drop games with no lines
    no_lines = [line.split(' (')[0] for line in lines_torv if '-' not in line]
    lines_torv = [line for line in lines_torv if '-' in line]

    home_torv = home_torv[:len(lines_torv)]
    away_torv = away_torv[:len(home_torv)]



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
    
    torv_df['Date'] = date
    
    
    if torv_final is not None:
        torv_final = pd.concat([torv_final, torv_df], axis = 0)
        
    else:
        torv_final = torv_df

    #close driver
    driver.close()



#join mapping df 
daily_final = pd.merge(daily_df,
                        mapping_df.rename(columns = {'Torv': 'Torv_Home'}),
                        left_on = 'home',
                        right_on = 'NCAABB')

daily_final = pd.merge(daily_final,
                        mapping_df.rename(columns = {'Torv':'Torv_Away'}),
                        left_on = 'road',
                        right_on = 'NCAABB')



#join with torvick data
final_df = pd.merge(daily_final, 
                    torv_final,
                    left_on = ['Torv_Home', 'Torv_Away', 'date'],
                    right_on = ['Home', 'Away', 'Date'])


#drop duplicates
final_df = final_df.drop_duplicates()

#drop columns that aren't needed
drops = ['Torv_Home', 'NCAABB_x', 'Torv_Away', 'NCAABB_y', 'Home', 'Away',
         'Torv_Home_Points', 'Torv_Away_Points', 'Date']
final_df = final_df[[column for column in final_df.columns if column not in drops]]


#join with merged df
concat_df = pd.concat([merged_df, final_df], axis = 0).reset_index(drop = True)


#map column names to get daily run columns
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


daily_merged = daily_merged.rename(mapping_dct, axis = 1)



#concatenate daily_merged
final_concat = pd.concat([concat_df,daily_merged], axis = 0).reset_index(drop = True)

#save output
final_concat.drop_duplicates().to_csv('./Data/merged_dataframe.csv')


    