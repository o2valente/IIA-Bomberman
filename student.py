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
bomb = (0,0)
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

        pos_ant = (0,0)
        way = []
        have_walls = True
        spawn = (1,1)
        enemy_on_sight = False
        waiting_for_enemies = False

        while True:
            try:
                state = json.loads(
                    await websocket.recv()
                )  # receive game state, this must be called timely or your game will get out of sync with the server4


######################################################################################################################################
                position = state['bomberman']
                x,y = position
                walls = state['walls']
                enemies = state['enemies']
                power_ups = state['powerups']

                if len(enemies) == 0:
                    pos_enemy = None
                else:
                    pos_enemy = get_enemies(state,position,enemies)['pos']
                
                if find_power_up(state,mapa) is None:
                    power_up_found = True
                else:
                    power_up_found = False

                if(len(walls) == 0):
                    if(len(enemies) != 0):
                        have_walls = False
                        if(not enemy_on_sight and not put_bomb and not power_up_found):
                            key = walk(position,find_power_up(state,mapa))
                            if(position == pos_ant):
                                key = change_path(position,mapa)
                        elif not enemy_on_sight and not put_bomb and position != [1,1] :
                            key = walk(position,spawn)
                            if(position == pos_ant):
                                key = change_path(position,mapa)
                            print("sending key:" + key)
                            # key = walk(position,intercept_enemie(pos_enemy))
                            # key = walk(position,pos_enemy)
                            if(position == pos_ant and position != [1,1]):
                                key = change_path(position,mapa)
                        elif position == [1,1]:
                            # waiting_for_enemies = True
                            key = ""
                            if calc_distance(position,pos_enemy) < 3:  
                                attack(position)
                            key = "B"    
                            way.append("d")
                            way.append("d")
                            way.append("s")
                            
                                # waiting_for_enemies = False
                            # if position == intercept_enemie(pos_enemy):
                            #     print("Attack>!!")
                            #     key = attack(position)
                    else:
                        key = walk(position,state['exit'])
                        if(position == pos_ant):
                            key = change_path(position,mapa)

                if len(walls) == 0:
                    have_walls = False
                else:
                    have_walls = True
                
                if way == []: 
                    put_bomb = False

                if(have_walls == True):
                    wall_closer = get_walls(state,position,mapa,walls)
                    key = walk(position,wall_closer)
                    if(position == pos_ant):
                        key = change_path(position,mapa)

                if(put_bomb == True):
                    key = way.pop()
                    if(calc_distance(position,bomb) > 5):
                       put_bomb = False
                
                if(pos_enemy != None):
                    if(calc_distance(position,pos_enemy) < 2 and not put_bomb):
                        enemy_on_sight = True
                        key = attack(position)
                    else:
                        enemy_on_sight = False
                
                if(calc_distance(position,wall_closer) == 1 and not put_bomb):
                    key = attack(position)

                    
                pos_ant = position
                
                if(put_bomb == False and key != ""):
                    way.append(memorize_path(key))
                
                

###################################################################################################################################################33

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
    if x <= 39 :
        return ( x + 10 , y )
    elif x > 39 and y >= 11 :
        return (49 , y - (x + 10 - 49))
    else :
        return (x - (10 - y), 1 )






def find_power_up(state,mapa):
    power_ups = state['powerups']
    for power  in power_ups:
        return power[0]

def memorize_path(key):
    if(key == "s"):
        return "w"
    if(key == "w"):
        return "s"
    if(key == "d"):
        return "a"
    if(key == "a"):
        return "d"

def attack(position):
    global put_bomb
    global bomb
    put_bomb = True
    bomb = position
    return "B"

def change_path(position,mapa):
    global direction
    direction = not direction
    return stuck_on_wall(position,mapa)
        

def walk(position,goal):
    global direction
    if direction == True :
        return get_to(position,goal)
    else:
        return get_to_y(position,goal)

def calc_distance(pos1,pos2):
    x1,y1 = pos1
    x2,y2 = pos2
    return math.sqrt(pow(x2-x1,2) + pow(y2-y1,2))

def get_to(pos1,pos2):
    x,y = pos1
    x_2,y_2 = pos2

    if(x < x_2):
        return "d"
    if(x > x_2):
        return "a"
    if(y > y_2):
        return "w"
    if(y < y_2):
        return "s"


def get_to_y(pos1,pos2):
    x,y = pos1
    x_2,y_2 = pos2

    if(y > y_2):
        return "w"
    if(y < y_2):
        return "s"
    if(x < x_2):
        return "d"
    if(x > x_2):
        return "a"
    

def stuck_on_wall(pos,mapa):
    x,y = pos
    if not mapa.is_stone((x+1,y)):
        return "d"
    if not mapa.is_stone((x,y+1)):
        return "w"
    if not mapa.is_stone((x-1,y)):
        return "a"
    if not mapa.is_stone((x,y-1)):
        return "s"

def get_walls(state,position,mapa,walls):
    min = 10000
    wall_len = len(state['walls'])
    if(wall_len != 0):
        for wall in walls:
            if not mapa.is_stone(wall):
                if(calc_distance(position,wall) < min):
                    min = calc_distance(position,wall)
                    wall_closer = wall
        return wall_closer

def get_enemies(state,position,enemies):
    min = 10000
    if(len(state['enemies']) != 0):
        for enemy in enemies:
            if calc_distance(position,enemy['pos']) < min:
                min = calc_distance(position,enemy['pos'])
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

