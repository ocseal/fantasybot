import os
import discord
import re
import requests
import pandas as pd
import string
import urllib.request
import sys
from bs4 import BeautifulSoup; 
client = discord.Client(); 

headers = requests.utils.default_headers()
headers.update({
  #'user-agent' : "Mozilla/5.0 (X11; CrOS x86_64 13505.63.0) AppleWebKit/537.36 (KHTML, like Gecko)"
  'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'
})

embedHelp = discord.Embed(title="Fantasy Bot Functions: **.fs**", description="Call the bot by typing '.fs ____'. Right now, the bot is set to provide fantasy basketball help. Make sure to include all punctuation in player names and to check your spelling. Currently, '.fs daily' is slow because one of the websites is making it harder for me to take its data.", color= 0xffffff)
embedHelp.add_field(name="Projected Rest-of-Season Rankings: **rank**", value="Type '.fs rank' followed by the last names, full names, or uncommon first names of the players you want to compare (separated by a comma).\n**Examples:** \n'.fs rank harden, davis' :ballot_box_with_check:\n'.fs rank giannis, kevin love' :ballot_box_with_check:", inline=False)
embedHelp.add_field(name="Projected Daily Points: **daily**", value="Type '.fs daily' followed by the last names, full names, or uncommon first names of the players you want to compare (separated by a comma).\n**Examples:**\n'.fs daily lillard, durant' :ballot_box_with_check:\n'.fs daily leonard, shai' :ballot_box_with_check:", inline=False)
embedHelp.add_field(name="For players that share a name or have a common last name, use full names or the highest-ranked player will be returned.", value= "**Example:** '.fs rank seth curry, stephen curry' :ballot_box_with_check:\n'.fs rank curry, anthony-towns' will provide results for Stephen Curry, not Seth Curry.")
playersNotFoundMessage = "One or both of your players couldn't be found. Check your spelling and comma placement."
p1notFound = "I don't recognize your first player. Check your spelling and comma placement."
p2notFound = "I don't recognize your second player. Check your spelling and comma placement."
notPlaying = "is not playing today."

@client.event
async def on_ready():
  print('Logged in as {0.user}'.format(client))

@client.event 
async def on_message(message):
  if message.author == client.user:
    return; 
  
  if message.content.startswith('.fs') or message.content.startswith('.Fs') or message.content.startswith('.FS') or message.content.startswith('.fS'):
    try: 
      wordList = re.sub("[^\w]", " ",  message.content).split()

      if message.content.lower() == '.fs':
        await message.channel.send(embed = embedHelp)
        return 
      
      if wordList[1].lower() == 'help':
        await message.channel.send(embed = embedHelp)
        return 
      
      if wordList[1].lower() == 'rank' or 'daily':
        injury = 'https://www.fantasypros.com/nba/rankings/ros-overall.php'
        seasonrank = 'https://www.fantasypros.com/nba/rankings/ros-overall-points-espn.php'

        injurypage = requests.get(injury)
        injurysoup = BeautifulSoup(injurypage.content, 'html.parser')
        injurytable = injurysoup.find('table', id = 'data')
        injurydf = pd.read_html(str(injurytable))[0]

        rankpage = requests.get(seasonrank); 
        soup = BeautifulSoup(rankpage.content, 'html.parser')
        table = soup.find('table', id = 'data'); 
        df = pd.read_html(str(table))[0]
        p1injury = False
        p2injury = False
        compare = True

        try: 
          p1, p2 = message.content.split(",")
          p1 = p1.title()
          p2 = p2.title()
          p1 = re.sub(r'[^\w\d\s\'-]+', '', p1).split()
          p2 = re.sub(r'[^\w\d\s\'-]+', '', p2).split()
          p1 = p1[2:]

        except ValueError:
          p1 = message.content
          p1 = p1.title()
          p1 = re.sub(r'[^\w\d\s\'-]+', '', p1).split()
          p1 = p1[2:]
          p2 = None
          compare = False

        try: 
          p1 = ['P.J.' if name == 'Pj' else name for name in p1]
          p1 = ['T.J.' if name == 'Tj' else name for name in p1]
          p1 = ['D.J.' if name == 'Dj' else name for name in p1]
          player1 = p1[0] + " " + p1[1]
          df1 = df[df["Player"].str.contains(player1, case = False, na = False)]
          
        except IndexError:
          p1 = ['LeBron' if name == 'James' else name for name in p1]
          player1 = p1[0]
          df1 = df[df["Player"].str.contains(player1, na=False, case= False)]

        try: 
          p2 = ['P.J.' if name == 'Pj' else name for name in p2]
          p2 = ['T.J.' if name == 'Tj' else name for name in p2]
          p2 = ['D.J.' if name == 'Dj' else name for name in p2]
          player2 = p2[0] + " " + p2[1]
          df2 = df[df["Player"].str.contains(player2, case = False, na = False)]
        except IndexError: 
          p2 = ['LeBron' if name == 'James' else name for name in p2]
          player2 = p2[0]
          df2 = df[df["Player"].str.contains(player2, na=False, case= False)] 
        except TypeError:
          pass

        if df1.dropna().empty:
            await message.channel.send(p1notFound)
            if p2 is None:
              return
            else:
              p1 = None
              compare = False
        else: 
          p1 = re.sub(r'\d+', '', df1["Player"].iloc[0])
          p1injdf = re.sub(r'\d+', '', injurydf["Player"].iloc[0])
          p1first, p1last = p1.split(" ", 1)
          p1last, p1misc = p1last.split(" ", 1)
          p1name = p1first + " " + p1last
          p1injurymessage = ""
          p1injuryemote = ""
          if p1injdf[-3:] == "OUT":
            p1injury = True
            p1injurymessage = " *He is currently injured.*"
            p1injuryemote = ":ambulance: "
          if p1injdf[-3:] == "DTD" :
            p1injurymessage = " *He is currently day-to-day/questionable.*"
            p1injuryemote = ":question: "

        try:
          if df2.dropna().empty:
            await message.channel.send(p2notFound)
            p2 = None
            compare = False
          else:
            p2 = re.sub(r'\d+', '', df2["Player"].iloc[0])
            p2injdf = re.sub(r'\d+', '', injurydf["Player"].iloc[0])
            p2first, p2last = p2.split(" ", 1)
            p2last, p2misc = p2last.split(" ", 1)
            p2name = p2first + " " + p2last
            p2injurymessage = ""
            p2injuryemote = ""
            if p2injdf[-3:] == "OUT":
              p2injury = True
              p2injurymessage = " *However, he is currently injured.*"
              p2injuryemote = ":ambulance: "
            if p2injdf[-3:] == "DTD" :
              p2injurymessage = " *However, he is currently day-to-day/questionable.*"
              p2injuryemote = ":question: "
        except:
          pass

        if wordList[1].lower() == 'rank':
          try: 
            p1bestrank = df1["Best"].iloc[0]
            p1worstrank = df1["Worst"].iloc[0]
            p1average = df1["Avg"].iloc[0]
            p1stddev = df1["Std Dev"].iloc[0]
            p1message = "According to experts, **" + p1name + "** " + p1injuryemote + "has a maximum overall rank of " + "**#" + str(p1bestrank) + "** and a minimum overall rank of **#" + str(p1worstrank) + "**.\nHis average rank is **" + str(p1average) + "** and his standard deviation is **" + str(p1stddev) + "**." + p1injurymessage
          except:
            compare = False
          if p2 is None:
            await message.channel.send(p1message)
            return 
          else: 
            p2bestrank = df2["Best"].iloc[0]
            p2worstrank = df2["Worst"].iloc[0]
            p2average = df2["Avg"].iloc[0]
            p2stddev = df2["Std Dev"].iloc[0]
            p2message = "**" + p2name + "** " + p2injuryemote + "has a maximum overall rank of " + "**#" + str(p2bestrank) + "** and a minimum overall rank of **#" + str(p2worstrank) + "**.\nHis average rank is **" + str(p2average) + "** and his standard deviation is **" + str(p2stddev) + "**." + p2injurymessage
            if compare:
              averagediff = p1average - p2average
              stddevdiff = p1stddev - p2stddev
              recfactor = (averagediff * (1.3)) + stddevdiff
              if recfactor < 0:
                p1message = p1message + " :white_check_mark:"
                p2message = p2message + " :no_entry:"
              elif recfactor > 0:
                p2message = p2message + " :white_check_mark:"
                p1message = p1message + " :no_entry:"
              else:
                p1message = p1message + " :ok:"
                p2message = p2message + " :ok:"
              await message.channel.send(p1message)
              await message.channel.send(p2message)
              return 
            else:
              await message.channel.send(p2message)
              return

        if wordList[1].lower() == 'daily':
          projpoints = 'https://www.fantasysp.com/projections/basketball/daily/'
          pointspage = urllib.request.urlopen(projpoints)
          soup1 = BeautifulSoup(pointspage, 'lxml')
          table1 = soup1.find('table'); 
          dfpoints = pd.read_html(str(table1))[0]

          if p1 is None and p2 is None:
            return

          if p1 is None or p2 is None:
            compare = False 

          try:
            dfp1 = dfpoints[dfpoints["Name"].str.contains(player1, case = False, na = False)]
          except: 
            compare = False
          
          try:
            dfp2 = dfpoints[dfpoints["Name"].str.contains(player2, case = False, na = False)]
          except:
            compare = False

          try: 
            if dfp1.empty:
              p1message = "**" + p1name + "** " + p1injuryemote + notPlaying + p1injurymessage
              p1points = 0
          except: 
            compare = False

          try: 
            if dfp2.empty:
              p2message = "**" + p2name + "** " + p2injuryemote + notPlaying + p2injurymessage
              p2points = 0
          except: 
            compare = False
            
          if p1 is not None: 
            try: 
              p1opp = dfp1.iloc[0, 2]
              p1opp, p1sched = p1opp.split(" ", 1)
              if '@' in p1opp:
                p1opp = p1opp[1:]
              p1points= dfp1.iloc[0, 18]
              p1message = "**" + p1name + "** " + p1injuryemote + "vs. " + p1opp + " : **" + str(p1points) + "** projected ESPN fantasy points." + p1injurymessage
              if p1injury == True:
                p1points = 0
            except:
              if dfp1.empty:
                pass
              else:
                compare = False

          if p2 is not None: 
            try: 
              p2opp = dfp2.iloc[0, 2]
              p2opp, p2sched = p2opp.split(" ", 1)
              if '@' in p2opp:
                p2opp = p2opp[1:]
              p2points = dfp2.iloc[0, 18]
              p2message = "**" + p2name + "** " + p2injuryemote + "vs. " + p2opp + " : **" + str(p2points) + "** projected ESPN fantasy points." + p2injurymessage
              if p2injury == True:
                p2points = 0
            except: 
              if dfp2.empty:
                pass
              else:
                compare = False
            
          if compare:
            if p1points > p2points:
              p1message = p1message + " :white_check_mark:"
              p2message = p2message + " :no_entry:"
            if p1points < p2points:
              p1message = p1message + " :no_entry:"
              p2message = p2message + " :white_check_mark:"
            if p1points == p2points and dfp1.empty is False and dfp2.empty is False:
              p1message == p1message + " :ok:"
              p2message == p2message + " :ok:"
            await message.channel.send(p1message)
            await message.channel.send(p2message)
            return 
          else:
            try: 
              if p2 is None:
                await message.channel.send(p1message)
                return 
            except:
              pass

            try: 
              if p1 is None:
                await message.channel.send(p2message)
                return 
            except:
              pass
      
    except:
      await message.channel.send("Are you sure you have the right syntax? Type '.fs' or '.fs help' to see what I can do.")
      return 

client.run('Nzk1MDE1NDgxNzU2NzQ1NzU5.X_DN3Q.7uT8071hSXk_N1b61zgIvZcwImw')
