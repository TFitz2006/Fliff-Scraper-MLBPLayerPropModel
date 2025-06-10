# Fliff-Scraper-MLBPLayerPropModel
Sports Betting Model/ Odds Scraper

This project aims to scrape player prop odds for MLB games on fliff.com and then compare those prop lines and odds with a somewhat rudementary model. The model uses statsMLB api to grab player season stas, past 3 games stats, and their head to head stats against the team theyre playing. Then based off a weighting algorthm the model produes its own estimated line for each of the players and their respective props. Finally it compares the Fliff line and the predicted line and ranks each of the props based on how favorable they are.

Planning to use fliff.com's 1$ of free fliff cash to track the the models success.
