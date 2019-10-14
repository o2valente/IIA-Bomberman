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

        while True:
            try:
                state = json.loads(
                    await websocket.recv()
                )  # receive game state, this must be called timely or your game will get out of sync with the server4
                
                position = state['bomberman']
                x,y = position
                walls = state['walls']
                
        ############################# teste #############################
                

               

                wall_closer = get_walls(position,mapa,walls)
                print(wall_closer)
                if direction == True :
                    key = get_to(position,wall_closer)
                else:
                    key = get_to_y(position,wall_closer)
                if(position == pos_ant):
                    key = stuck_on_wall(position,mapa)
                    direction = not direction

                if(put_bomb == False):
                    if(key == "s"):
                        way.append("w")
                    if(key == "w"):
                        way.append("s")
                    if(key == "d"):
                        way.append("a")
                    if(key == "a"):
                        way.append("d")

                if(put_bomb == True):
                    key = way.pop()
                    if way == []:
                        put_bomb =False
                   
                if(calc_distance(position,wall_closer) == 1 and put_bomb == False):
                    put_bomb = True
                    key = "B"
                    
                pos_ant = position

                print(key) 
                    
    ###############################################################################

                # Next lines are only for the Human Agent, the key values are nonetheless the correct ones!
                # await websocket.send(
                #             json.dumps({"cmd": "key", "key": key})
                #         ) 

                # for event in pygame.event.get():
                #     if event.type == pygame.QUIT or not state["lives"]:
                #         pygame.quit()

                #     if event.type == pygame.KEYDOWN:
                #         if event.key == pygame.K_UP:
                #             key = "w"
                #         elif event.key == pygame.K_LEFT:
                #             key = "a"
                #         elif event.key == pygame.K_DOWN:
                #             key = "s"
                #         elif event.key == pygame.K_RIGHT:
                #             key = "d"
                #         elif event.key == pygame.K_a:
                #             key = "A"
                #         elif event.key == pygame.K_b:
                #             key = "B"

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

def get_walls(position,mapa,walls):
    min = 10000
    for wall in walls:
        if not mapa.is_stone(wall):
            if(calc_distance(position,wall) < min):
                min = calc_distance(position,wall)
                wall_closer = wall
    return wall_closer

# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='bombastico' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))

