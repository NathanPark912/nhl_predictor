import requests
import pandas as pd
import datetime
#get yesterdays date
todays_date = datetime.date.today()
yesterdays_date = todays_date - datetime.timedelta(days=1)
yesterdays_date = yesterdays_date.strftime('%Y-%m-%d')
print(yesterdays_date)

API_URL = "https://statsapi.web.nhl.com/api/v1"
# fetch game list
response = requests.get(API_URL + "/schedule?startDate=" + yesterdays_date + "&endDate=" + yesterdays_date, params={"Content-Type": "application/json"})
data = response.json()
# loop through dates
game_keys = []
for date in data["dates"]:
    print("--- Date:", date["date"])
    # and now through games
    for game in date["games"]:
        game_keys.append(game["gamePk"])

away_teams = []
away_goalies = []
away_goals = []
home_teams = []
home_goalies = []
home_goals = []
for keys in game_keys:
    response = requests.get(API_URL + "/game/" + str(keys) + "/feed/live", params={"Content-Type": "application/json"})
    data = response.json()
    
    away_teams.append(data["liveData"]["boxscore"]["teams"]["away"]["team"]["abbreviation"])
    away_goals.append(data["liveData"]["boxscore"]["teams"]["away"]["teamStats"]["teamSkaterStats"]["goals"])
    
    home_teams.append(data["liveData"]["boxscore"]["teams"]["home"]["team"]["abbreviation"])
    home_goals.append(data["liveData"]["boxscore"]["teams"]["home"]["teamStats"]["teamSkaterStats"]["goals"])
    
    
    away_goalieID = data["liveData"]["boxscore"]["teams"]["away"]["goalies"][-1]
    home_goalieID = data["liveData"]["boxscore"]["teams"]["home"]["goalies"][-1]
    #get goalie names
    away_url = requests.get(API_URL + "/people/" + str(away_goalieID), params={"Content-Type": "application/json"})
    away_data = away_url.json()
    away_goalie_name = away_data["people"][0]["fullName"]
    home_url = requests.get(API_URL + "/people/" + str(home_goalieID), params={"Content-Type": "application/json"})
    home_data = home_url.json()
    home_goalie_name = home_data["people"][0]["fullName"]
    
    away_goalies.append(away_goalie_name)
    home_goalies.append(home_goalie_name)
df = pd.DataFrame()

df['away_team'] = away_teams
df['away_goalie'] = away_goalies
df['away_goals'] = away_goals
df['home_team'] = home_teams
df['home_goalie'] = home_goalies
df['home_goals'] = home_goals

#this df is all of the starting goalies for yesterdays games
tables = pd.read_html('Matchups'+yesterdays_date+'.html')
winners=[]
for index, row in df.iterrows():
    if row.home_goals > row.away_goals:
        winner = row.home_team
    else:
        winner = row.away_team
    winners.append(winner)
df['winner'] = winners


def check_pick(row,my_table):
    if row.home_goalie == column_headers[1]:
        home_index = 1
    elif row.home_goalie == column_headers[2]:
        home_index = 2
    else:
        return 'undefined'
    if row.away_goalie == my_table.iloc[0,0]:
        away_index = 0
    elif row.away_goalie == my_table.iloc[1,0]:
        away_index = 1
    else:
        return 'undefined'
    
    prediction = my_table.iloc[away_index,home_index]
    predicted = prediction.split('(')
    return predicted[0]

prediction = []
for index, row in df.iterrows():
    for i in range(len(tables)):
        my_table = tables[i]
        column_headers = my_table.columns.values.tolist()
        teams = column_headers[0].split(' ')
        
        if row.away_team == teams[0]:
            prediction.append(check_pick(row,my_table))
            
df['Prediction'] = prediction
result = []
df = df[df.Prediction != 'undefined']

for index, row in df.iterrows():
    if row.Prediction == row.winner:
          result.append(1)
    else:
            result.append(0)
df['results'] = result
print(df)
with pd.ExcelWriter("model_performance.xlsx",
    mode="a",
    engine="openpyxl",
    if_sheet_exists="new",
) as writer:
    df.to_excel(writer, sheet_name=yesterdays_date)
        
              