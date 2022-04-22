#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 10 18:57:38 2022

@author: Broth
"""
#import packages
import os
import pandas as pd
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By


base_files = [file for file in os.listdir(os.getcwd() + '/Data/') if 'ncaabb' in file]

ncaabb_final = None

for file in base_files:
    if ncaabb_final is not None:
        ncaabb_df = pd.read_csv(os.getcwd() + '/Data/' + file )
        ncaabb_final = pd.concat([ncaabb_final, ncaabb_df], axis = 0)
    else:
        ncaabb_final = pd.read_csv(os.getcwd() + '/Data/' + file)

#drop nulls from ncaabb
ncaabb_final = ncaabb_final[ncaabb_final.home.notnull()].reset_index(drop = True)

torv_final = None

for date in [date for date in ncaabb_final.date.unique() if isinstance(date, str)]:
    
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


#match torvick lines to ncaabb lines
torv_final.Torv_Line = np.where(torv_final.Home > torv_final.Away, torv_final.Torv_Line, -1*torv_final.Torv_Line)



#load in mapping dataset
mapping_df = pd.read_csv('./Data/CBB_Matching.csv')

#join mapping df 
ncaabb_final = pd.merge(ncaabb_final,
                        mapping_df.rename(columns = {'Torv': 'Torv_Home'}),
                        left_on = 'home',
                        right_on = 'NCAABB')

ncaabb_final = pd.merge(ncaabb_final,
                        mapping_df.rename(columns = {'Torv':'Torv_Away'}),
                        left_on = 'road',
                        right_on = 'NCAABB')



#join with torvick data
final_df = pd.merge(ncaabb_final, 
                    torv_final,
                    left_on = ['Torv_Home', 'Torv_Away', 'date'],
                    right_on = ['Home', 'Away', 'Date'])


#drop duplicates
final_df = final_df.drop_duplicates()

#drop columns that aren't needed
drops = ['Torv_Home', 'NCAABB_x', 'Torv_Away', 'NCAABB_y', 'Home', 'Away',
         'Torv_Home_Points', 'Torv_Away_Points', 'Date']
final_df = final_df[[column for column in final_df.columns if column not in drops]]



#save final dataframe
final_df.drop_duplicates().reset_index(drop = True).to_csv('./Data/merged_dataframe.csv')
    


