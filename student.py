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

        pos_ant = (0,0)
        direction = True
        put_bomb = False
        way = []
        have_walls = True

        while True:
            try:
                state = json.loads(
                    await websocket.recv()
                )  # receive game state, this must be called timely or your game will get out of sync with the server4
                
                position = state['bomberman']
                x,y = position
                walls = state['walls']
                enemies = state['enemies']

                
                wall_len = len(state['walls'])

                
                pos_enemy = get_enemies(state,position,enemies)['pos']
                


                spawn = 1,1

                if(wall_len == 0):
                    if(len(enemies) != 0):
                        print("Não há paredes")
                        have_walls = False
                        if direction == True :
                            key = get_to(position,spawn)
                        else:
                            key = get_to_y(position,spawn)
                        if(position == pos_ant):
                            key = stuck_on_wall(position,mapa)
                            direction = not direction
                        print("Estou a ir")
                        if(state['bomberman'] == [1,1] and not put_bomb):
                            print("im here")
                            put_bomb = True
                            print("put bomb")
                            key = "B"
                            print("key b")
                            bomb = position
                    else:
                        if direction == True :
                            key = get_to(position,state['exit'])
                        else:
                            key = get_to_y(position,state['exit'])
                        if(position == pos_ant):
                            key = stuck_on_wall(position,mapa)
                            direction = not direction
                
                if way == []: 
                    put_bomb = False
                
               
                
                if(have_walls == True and wall_len != 0):
                    wall_closer = get_walls(state,position,mapa,walls)

                    if direction == True :
                        key = get_to(position,wall_closer)
                    else:
                        key = get_to_y(position,wall_closer)
                    if(position == pos_ant):
                        key = stuck_on_wall(position,mapa)
                        direction = not direction

                if(put_bomb == True):
                    print("Bomba")
                    key = way.pop()
                    if(calc_distance(position,bomb) > 5):
                       #key = ""
                       put_bomb = False
                
                if(pos_enemy != None):
                    if(calc_distance(position,pos_enemy) < 3 and not put_bomb):
                        #x_e,y_e = pos_enemy
                        #get_to(position,(x_e+5,y_e+5))
                        put_bomb = True
                        key = "B"
                        bomb = position
                


                # print(calc_distance(position,pos_enemy))
                
                   
                if(calc_distance(position,wall_closer) == 1 and not put_bomb):
                    put_bomb = True
                    key = "B"
                    bomb = position

                    
                pos_ant = position
                
                if(put_bomb == False):
                    if(key == "s"):
                        way.append("w")
                    if(key == "w"):
                        way.append("s")
                    if(key == "d"):
                        way.append("a")
                    if(key == "a"):
                        way.append("d")
                
                print("Sending key:" + key)

                await websocket.send(
                    json.dumps({"cmd": "key", "key": key})
                )  # send key command to server - you must implement this send in the AI agent
                # break
            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return

            # Next line is not needed for AI agent
        #    pygame.display.flip()


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

