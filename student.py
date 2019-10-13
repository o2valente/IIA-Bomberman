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

        while True:
            try:
                state = json.loads(
                    await websocket.recv()
                )  # receive game state, this must be called timely or your game will get out of sync with the server4
                

                position = state['bomberman']
                x,y = position
                walls = state['walls']
                


        ############################# teste #############################
                
                if y == 1:
                    key = "d"
                if x == 9:
                    key = "s"
                for wall in walls:
                    calc_distance((1,1),(2,2))
                    print(calc_distance(position,wall))
                    if(calc_distance(position,wall) <= 1):
                        if not mapa.is_stone(wall):
                            key = "B"

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

# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='bombastico' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))





