import sys
import json
import asyncio
import websockets
import getpass
import os
import math

from mapa import Map

# Next 2 lines are not needed for AI agent
# import pygame

# pygame.init()

direction = True
put_bomb = False
bomb = (0, 0)
power_up_found = False


async def agent_loop(server_address="localhost:8000", agent_name="student"):
    async with websockets.connect(f"ws://{server_address}/player") as websocket:

        # Receive information about static game properties
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))
        msg = await websocket.recv()
        game_properties = json.loads(msg)

        # You can create your own map representation or use the game representation:
        mapa = Map(size=game_properties["size"], mapa=game_properties["map"])

        # Next 3 lines are not needed for AI agent
        # SCREEN = pygame.display.set_mode((299, 123))
        # SPRITES = pygame.image.load("data/pad.png").convert_alpha()
        # SCREEN.blit(SPRITES, (0, 0))

        # direction = True
        global direction
        global put_bomb
        global bomb
        global power_up_found

        pos_ant = (0, 0)
        way = []
        have_walls = True
        spawn = (1, 1)
        enemy_on_sight = False
        waiting_for_enemies = False
        wait_for_bomb = False
        fase = 1

        while True:
            try:
                state = json.loads(
                    await websocket.recv()
                )  # receive game state, this must be called timely or your game will get out of sync with the server4

                ######################################################################################################################################
                position = state['bomberman']                                                               # Bomberman's position
                x, y = position                                                                              

                walls = state['walls']                                                                      # Walls's position
                enemies = state['enemies']                                                                  # Enemy's position
                power_ups = state['powerups']                                                               # Power-Ups's position

                if len(enemies) == 0:                                                                       # Get position of closest enemy
                    pos_enemy = None
                else:
                    pos_enemy = get_enemies(state, position, enemies)['pos']

                if find_power_up(state, mapa) is None:                                                       # Already found power-up?
                    power_up_found = True
                else:
                    power_up_found = False

################################## No Walls ########################################################################
                if len(walls) == 0:                                                                         # If walls are all destroyed
                    print("No walls")
                    have_walls = False

                    if len(enemies) != 0:                                                                   # If there are still enemies
                        if not put_bomb and not power_up_found:                                             # if bomb is not planted and power-up not found yet
                            key = walk(position,find_power_up(state,mapa))                                  # Get power-up
                            if position == pos_ant:
                                key = change_path(position,mapa)
                        elif  not put_bomb and position != [1,1]:                                                                 # If power-up is found
                            print("What am I doing?")
                            key = walk(position,[1,1])                                                      # Walk to spawn
                            if position == pos_ant:
                                key = change_path(position,mapa)
                        elif position == [1,1] and calc_distance(position, pos_enemy) > 4 and not put_bomb:
                            waiting_for_enemies = True
                        elif position == [1,1] and calc_distance(position,pos_enemy) < 4:
                            if fase == 1:
                                key = "s"
                            elif fase == 2:
                                key = "s" 
                            elif fase == 3:
                                key = "d"
                            fase += 1
                    else:                                                                                   # If enemies are all dead  
                        key = walk(position, state['exit'])                                                 # Go to exit
                        if position == pos_ant:
                            key = change_path(position, mapa)
                
###############################################################################################################
############################################### With Walls ####################################################
                else:                  # If walls exist
                
                    if not way:
                        put_bomb = False

                    wall_closer = get_walls(state, position, mapa, walls)                               # Get closer wall

                    key = walk(position, wall_closer)                                                   # walk to the closest wall
                    if position == pos_ant:
                        key = change_path(position, mapa)

                    if put_bomb:                                                                        # Run from bomb
                        key = way.pop()
                        # key = walk(position,is_safe(position,mapa,enemies,0,False))
                        if calc_distance(position, bomb) > 4:
                            put_bomb = False
                            wait_for_bomb = True
                    
                    if pos_enemy is not None:                                                           # If run into an enemy, attack
                        if calc_distance(position, pos_enemy) < 3 and not put_bomb and len(way) > 4:
                            enemy_on_sight = True
                            key = attack(position)
                        else:
                            enemy_on_sight = False
                            # if calc_distance(position, bomb) > 5:
                            #     put_bomb = False

                    if calc_distance(position, wall_closer) == 1 and not put_bomb and len(way) > 4:     # attack a wall
                        key = attack(position)

####################################################################################################################
############################################ WITH OR WITHOUT WALLS #################################################
                pos_ant = position                                                                      # Guardar posição anterior

                if put_bomb is False and key != "":                                                     #Memorizar caminho
                    way.append(memorize_path(key))
                
                if key is None or waiting_for_enemies == True:                                                # Ficar parado
                    if key is None:
                        key = ""
                        wait_for_bomb = False

                print(key)

##################################################################################################################################################

                await websocket.send(
                    json.dumps({"cmd": "key", "key": key})
                )  # send key command to server - you must implement this send in the AI agent
                # break
            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return

            # Next line is not needed for AI agent
        #    pygame.display.flip()

def intercept_enemie(pos_enemy):
    x,y = pos_enemy
    if x <= 47 :
        return ( x + 3 , y )
    elif x > 46 and y >= 2 :
        return (49 , y - (x + 3 - 49))
    else :
        return (x - (3 - y), 1 )

def intercept_enemy(pos_enemy):
    x, y = pos_enemy
    if x <= 42:
        return x + 7, y
    elif x > 46 and y >= 3:
        return 49, y - (x + 7 - 49)
    else:
        return x - (7 - y), 1

# def is_safe(position,mapa,enemies,step,turn_back):
#     x,y = position
#     step += 1
#     if step == 4:
#         return position
#     if not mapa.is_stone((x+1,y)) and not mapa.is_blocked((x+1,y)) and turn_back == False:
#         print("Direita")
#         return is_safe((x+1,y),mapa,enemies,step,turn_back)
#     elif not mapa.is_stone((x-1,y)) and not mapa.is_blocked((x-1,y)):
#         turn_back = True
#         print("Esquerda")
#         return is_safe((x-1,y),mapa,enemies,step,turn_back)
#     elif not mapa.is_stone((x,y+1)) and not mapa.is_blocked((x,y+1)):
#         turn_back = False
#         print("Down")
#         return is_safe((x,y+1),mapa,enemies,step,turn_back)
#     elif not mapa.is_stone((x,y-1)) and not mapa.is_blocked((x,y-1)):
#         turn_back = False
#         print("Up")
#         return is_safe((x,y-1),mapa,enemies,step,turn_back)

# def run_way(position,mapa):
#     x,y = position
#     if mapa.map[x,y+1] == 1 and mapa.map[x,y-1] == 1:
#         if mapa.map[x-1,y+1] == 1:
#             return run_to_up()
#         else:
#             return run_to_down()
#     else:
#         if mapa.map[x-1,y] == 1:
#             return run_to_right()
#         else:
#             return run_to_left()

# def run_to_up():
#     run = []
#     run.append("w")
#     run.append("w")
#     run.append("a")
#     return run

# def run_to_down():
#     run = []
#     run.append("s")
#     run.append("s")
#     run.append("a")
#     return run

# def run_to_right():
#     run = []
#     run.append("s")
#     run.append("d")
#     run.append("d")
#     return run

# def run_to_left():
#     run = []
#     run.append("s")
#     run.append("a")
#     run.append("a")
#     return run

def find_power_up(state, mapa):
    power_ups = state['powerups']
    for power in power_ups:
        return power[0]


def memorize_path(key):
    if key == "s":
        return "w"
    if key == "w":
        return "s"
    if key == "d":
        return "a"
    if key == "a":
        return "d"


def attack(position):
    global put_bomb
    global bomb
    put_bomb = True
    bomb = position
    return "B"


def change_path(position, mapa):
    global direction
    direction = not direction
    return stuck_on_wall(position, mapa)


def walk(position, goal):
    global direction
    if direction:
        return get_to(position, goal)
    else:
        return get_to_y(position, goal)


def calc_distance(pos1, pos2):
    x1, y1 = pos1
    x2, y2 = pos2
    return math.sqrt(pow(x2 - x1, 2) + pow(y2 - y1, 2))


def get_to(pos1, pos2):
    x, y = pos1
    x_2, y_2 = pos2

    if (x < x_2):
        return "d"
    if (x > x_2):
        return "a"
    if (y > y_2):
        return "w"
    if (y < y_2):
        return "s"


def get_to_y(pos1, pos2):
    x, y = pos1
    x_2, y_2 = pos2

    if y > y_2:
        return "w"
    if y < y_2:
        return "s"
    if x < x_2:
        return "d"
    if x > x_2:
        return "a"


def stuck_on_wall(pos, mapa):
    x, y = pos
    if not mapa.is_stone((x + 1, y)):
        return "d"
    if not mapa.is_stone((x, y + 1)):
        return "w"
    if not mapa.is_stone((x - 1, y)):
        return "a"
    if not mapa.is_stone((x, y - 1)):
        return "s"


def get_walls(state, position, mapa, walls):
    min = 10000
    wall_len = len(state['walls'])
    if wall_len != 0:
        for wall in walls:
            if not mapa.is_stone(wall):
                if calc_distance(position, wall) < min:
                    min = calc_distance(position, wall)
                    wall_closer = wall
        return wall_closer


def get_enemies(state, position, enemies):
    min = 10000
    if len(state['enemies']) != 0:
        for enemy in enemies:
            if calc_distance(position, enemy['pos']) < min:
                min = calc_distance(position, enemy['pos'])
                enemy_closer = enemy
    else:
        enemy_closer = None
    return enemy_closer


# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='bombastico' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))
