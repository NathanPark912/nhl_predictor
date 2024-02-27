import requests
import pandas as pd
import datetime
def get_abv(links):
    abvs = []
    team_url = "https://api-web.nhle.com/v1/"
    for link in links:
        response = requests.get(team_url + link, params={"Content-Type": "application/json"})
        data = response.json()
        for team in data['teams']:
            abvs.append(team["abbreviation"])
    return abvs

def create_schedule():
    matchups = []

    todays_date = datetime.date.today()
    todays_date = todays_date.strftime('%Y-%m-%d')
    response = requests.get("https://api-web.nhle.com/v1/schedule/now", params={"Content-Type": "application/json"})
    data = response.json()

    for game in data["gameWeek"][0]["games"]:
        matchup = {
            "AwayTicker": game["awayTeam"]["abbrev"],
            "HomeTicker": game["homeTeam"]["abbrev"]
        }
        matchups.append(matchup)
    schedule = pd.DataFrame(matchups)
    return schedule

import json
from io import StringIO

from scipy.stats import poisson

response = requests.get("https://moneypuck.com/moneypuck/playerData/seasonSummary/2023/regular/skaters.csv")
s=str(response.content,'utf-8')

data = StringIO(s) 

df=pd.read_csv(data)

df = df[df['situation'] == 'all']
df['shots_per_game'] = df['I_F_shotAttempts'] / df['games_played']
df['misses_per_game'] = df['I_F_missedShots'] / df['games_played']
df['shots_blocked_per_game'] = df['shotsBlockedByPlayer'] / df['games_played']
df['icetime_weight'] = df['icetime'] / df['games_played']
df['hits_per_game'] = df['I_F_hits'] / df['games_played']
##################################################################################

##################################################################################
def stat_producer(team):
  temp_df = df[df.team == team]
  temp_df = temp_df.sort_values(by='icetime_weight', ascending=False)

  tm_shots = temp_df['shots_per_game'].iloc[0:18].sum()
  tm_shots_missed = temp_df['misses_per_game'].iloc[0:18].sum()
  tm_shots_blocked = temp_df['shots_blocked_per_game'].iloc[0:18].sum()

  tm_hits = temp_df['hits_per_game'].iloc[0:18].sum()

  return tm_shots, tm_hits, tm_shots_blocked, tm_shots_missed

#Input method of calculation wanted
def run_game(home_team, away_team,home_goalie,away_goalie,style):
  #put the goalie save % as a row in the schedule df, creating multiple games for 
  away_shots, away_hits, away_shots_blocked, away_shots_missed = stat_producer(away_team)
  home_shots, home_hits, home_shots_blocked, home_shots_missed = stat_producer(home_team)


  if style == 'Decision Tree':
    away_df = pd.DataFrame()
    home_df = pd.DataFrame()

    #set up away df for predicitons
    away_df['HoA'] = [0]
    away_df['shots_x'] = [44.0]
    away_df['hits'] = [11.8]
    away_df['blocked'] = [11.0]
    away_df['savePercentage'] = [.96]

    away_prediction = forest.predict(away_df)
    #set up home df for predictions
    home_df['HoA'] = [1]
    home_df['shots_x'] = home_shots - home_shots_missed
    home_df['hits'] = home_hits
    home_df['blocked'] = home_shots_blocked
    home_df['savePercentage'] = .92

    home_prediction = forest.predict(home_df)

    print(away_prediction, home_prediction)
  if style == 'Sheet':
    home_goals = (home_shots - home_shots_missed - away_shots_blocked) * (1 - away_goalie)
    away_goals = (away_shots - away_shots_missed - home_shots_blocked) * (1 - home_goalie)

    home_score = poisson.rvs(home_goals, size = 10000)
    away_score = poisson.rvs(away_goals, size = 10000)

    homeWin = 0
    awayWin = 0
    tie = 0

    for i in range(len(home_score)):
      if home_score[i] > away_score[i]:
        homeWin += 1
      elif home_score[i] < away_score[i]:
        awayWin += 1
      else:
        tie += 1
    
    homeWinPer = (homeWin + (tie/2)) / 10000
    awayWinPer = (awayWin + (tie/2)) / 10000
    tiePer = tie/10000

    homeWinPer = "{:.1%}".format(homeWinPer)
    awayWinPer = "{:.1%}".format(awayWinPer)
    tiePer = "{:.1%}".format(tiePer)

    if home_goals > away_goals:
      winner = home_team + '(' + homeWinPer + '/' + str(round(home_goals,2)) + '/' + str(round(away_goals,2)) + ')'
    else:
      winner = away_team + '(' + awayWinPer + '/' + str(round(home_goals,2)) + '/' + str(round(away_goals,2)) + ')'

      
  return winner


response = requests.get("https://moneypuck.com/moneypuck/playerData/seasonSummary/2023/regular/goalies.csv")
s=str(response.content,'utf-8')

data = StringIO(s) 

goalie_df=pd.read_csv(data)

goalie_df = goalie_df[goalie_df.iloc[:,5] == 'all']
goalie_df['savePercentage'] = 1.0 - goalie_df.iloc[:,9] / goalie_df.iloc[:,16]

import itertools
from itertools import permutations

def goalie_combinations(team1, team2):
  tm1 = goalie_df[goalie_df.iloc[:,3] == team1]
  tm2 = goalie_df[goalie_df.iloc[:,3] == team2]

  tm1 = tm1.sort_values(by=tm1.columns[7],ascending=False)
  tm2 = tm2.sort_values(by=tm2.columns[7],ascending=False)

  try:
    secondGoalietm1 = (tm1.iloc[1,2],tm1.iloc[1,36])
  except:
    secondGoalietm1 = ("no goalie",.60)
  try:
    secondGoalietm2 = (tm2.iloc[1,2],tm2.iloc[1,36])
  except:
    secondGoalietm2 = ("no goalie",.60)

  team_1_list = [(tm1.iloc[0,2],tm1.iloc[0,36]),secondGoalietm1]
  team_2_list = [(tm2.iloc[0,2],tm2.iloc[0,36]),secondGoalietm2]

  combos = list(itertools.product(team_1_list, team_2_list))

  return combos


def run_todays_games():
    todays_games = create_schedule()
    todays_date = datetime.date.today()
    todays_date = todays_date.strftime('%Y-%m-%d')
    filler =''
    for index, row in todays_games.iterrows():
        away_team = row.AwayTicker
        home_team = row.HomeTicker

        goalie_combos = goalie_combinations(away_team,home_team)
        game_df = pd.DataFrame()
        goalie22 = goalie_combos[0][0][0]
        goalie11 = goalie_combos[2][0][0]

        index_labels = [goalie22, goalie11]
        game_df = pd.DataFrame(index=index_labels)
        game_df = game_df.rename_axis(columns=away_team + " at " + home_team)
        goalie1 = goalie_combos[0][1][0]

        goalie2 = goalie_combos[1][1][0]
        game_df[goalie1] = ""
        game_df[goalie2] = ""

        game_df.iloc[0,0] = run_game(home_team, away_team,goalie_combos[0][1][1],goalie_combos[0][0][1],"Sheet")
        game_df.iloc[0,1] = run_game(home_team, away_team,goalie_combos[1][1][1],goalie_combos[1][0][1],"Sheet")
        game_df.iloc[1,0] = run_game(home_team, away_team,goalie_combos[2][1][1],goalie_combos[2][0][1],"Sheet")
        game_df.iloc[1,1] = run_game(home_team, away_team,goalie_combos[3][1][1],goalie_combos[3][0][1],"Sheet")
    
        table = game_df.to_html(classes='table table-stripped')
        table = table +"\n<br /><br />"
        text_file = open('Matchups'+todays_date+'.html', 'a')
        text_file.write(table)
        text_file.close()
        filler = filler + table
        print(game_df)
    return filler
final_df = run_todays_games()


#########################################adding in player props
response = requests.get("https://moneypuck.com/moneypuck/playerData/seasonSummary/2023/regular/teams.csv")
s=str(response.content,'utf-8')

data = StringIO(s) 

team_df=pd.read_csv(data)

team_df = team_df[team_df['situation'] == 'all']
team_df['shots_against_pg'] = team_df['shotsOnGoalAgainst'] / team_df['games_played']
team_df['shots_for_pg'] = team_df['shotsOnGoalFor'] / team_df['games_played'] 
team_df.head()

player_df = df

player_df['SOG per game'] = player_df['I_F_shotsOnGoal'] / player_df['games_played']
player_df = player_df.merge(team_df, how='left', left_on=['team'], right_on=['team'])
player_df['shot_portion'] = player_df['SOG per game'] / player_df['shots_for_pg']
player_df.head()


def player_props(team1,team2):
  tm1_df = player_df[player_df.team == team1]
  tm2_df = player_df[player_df.team == team2]

  tm1_shots_allowed = team_df.loc[team_df['team'] == team1, 'shots_against_pg'].iloc[0]
  tm2_shots_allowed = team_df.loc[team_df['team'] == team2, 'shots_against_pg'].iloc[0]
  tm1_df['shot_share'] = tm1_df['shot_portion'] * tm2_shots_allowed
  tm2_df['shot_share'] = tm2_df['shot_portion'] * tm1_shots_allowed
  print(tm1_df['shot_share'])
  print(tm2_shots_allowed)
  tm1_df['difference'] = tm1_df['shot_share'] - tm1_df['SOG per game']
  tm2_df['difference'] = tm2_df['shot_share'] - tm2_df['SOG per game']
  print(tm1_df['SOG per game'])
  print(tm1_df['difference'] )
  tm1_df = tm1_df[['team','name_x','SOG per game','shot_share','difference']]
  tm2_df = tm2_df[['team','name_x','SOG per game','shot_share','difference']]

  tm1_df = tm1_df.sort_values(by=['difference'],ascending=False)
  tm2_df = tm2_df.sort_values(by=['SOG per game'],ascending=False)

  match_df = tm1_df.append(tm2_df, ignore_index=True)
  #odds
  oddsfor2 = []
  oddsfor3 = []
  oddsfor4 = []
  for j in range(len(match_df['name_x'])):
    projected_shots = poisson.rvs(match_df['shot_share'].iloc[j], size = 10000)

    above2_5 = 0
    above1_5 = 0
    above3_5 = 0

    for i in range(len(projected_shots)):
      if projected_shots[i] > 3:
        above3_5 += 1
      elif projected_shots[i] > 2:
        above2_5 += 1
      elif projected_shots[i] > 1:
        above1_5 += 1
    two = (above3_5 + above2_5 + above1_5) / 10000
    three = (above3_5 + above2_5) / 10000
    four = (above3_5) / 10000
    oddsfor2.append(two)
    oddsfor3.append(three)
    oddsfor4.append(four)
  match_df['odds for 2'] = oddsfor2
  match_df['odds for 3'] = oddsfor3
  match_df['odds for 4'] = oddsfor4

  match_df = match_df.sort_values(by=['SOG per game'],ascending=False)
  
  match_df = match_df.set_index('team')
  return match_df.iloc[0:10,:]

def run_todays_games_props():
  todays_games = create_schedule()
  todays_date = datetime.date.today()
  todays_date = todays_date.strftime('%Y-%m-%d')
  filler =''
  for index, row in todays_games.iterrows():
    away_team = row.AwayTicker
    home_team = row.HomeTicker
    
    props = player_props(home_team,away_team)
    table2 = props.to_html(classes='table table-stripped')
    table2 = table2 +"\n<br /><br />"
    text_file = open('props'+todays_date+'.html', 'a')
    text_file.write(table2)
    text_file.close()
    filler = filler + table2
  return filler

props_html = run_todays_games_props()

def send_emails(htmlcode):
    import os
    import smtplib
    import imghdr
    from email.message import EmailMessage
    #this works for emailing it out
    email = 'nathanpark912@gmail.com'
    password = 'You thought'

    from email.mime.multipart import MIMEMultipart #pip install email-to
    from email.mime.text import MIMEText
    from email.mime.image import MIMEImage
    from email.mime.application import MIMEApplication

    contacts = ['parknathan12@yahoo.com','parknick98@gmail.com','jakeraymer@gmail.com', 'danobs29@gmail.com','brettlee44@comcast.net']
    #contacts = ['parknathan12@yahoo.com']
    msg = EmailMessage()
    msg['Subject'] = 'Todays Picks'
    msg['From'] = email
    msg['To'] = (", ").join(contacts)

    text_part = msg.iter_parts()
    text_part
    msg.add_alternative(htmlcode, subtype='html')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(email, password)
        smtp.send_message(msg)
        
send_emails(final_df + props_html)
    
