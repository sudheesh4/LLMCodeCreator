from UTILS  import *


prompt="we want to make a website to play tic-tac-toe. we want to use only HTML JS CSS."
#prompt="we want to make a python program to play tic-tac-toe."
#prompt="We want to make a simple website with multiple pages, to display text and images.we want to use only HTML JS CSS."


team=AgentTeam(prompt)


codes=team.run()


savelogs(team)

savetofiles(codes[-1].content)

