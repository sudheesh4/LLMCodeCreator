from UTILS  import *


prompt="we want to make a website to play tic-tac-toe. we want to use only HTML JS CSS."
#prompt="we want to make a python program to play tic-tac-toe."
#prompt="We want to make a simple website with multiple pages, to display text and images. We want dummy text to be filled #in. We want navigation. Keep the design pretty and vibrant .we want to use only HTML JS CSS."
#prompt="We want to make a python program to solve PDE using finite element."
#prompt="We want to make a website to play snake game. We want to use only HTML CSS JS."

team=AgentTeam(prompt)


codes=team.run()


savelogs(team)

savetofiles(team,codes[-1].content)

