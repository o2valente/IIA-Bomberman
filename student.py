import sys
import json
import asyncio
import websockets
import getpass
import os
import math
import astar

from mapa import Map

# Next 2 lines are not needed for AI agent
# import pygame

# pygame.init()

direction = True
put_bomb = False
run = False
wait = 0
power_up_found = False


##############################################################################################################################################
##############################################################################################################################################
##############################################################################################################################################
##############################################################################################################################################
##############################################################################################################################################
##############################################################################################################################################
##############################################################################################################################################
###########                      CORRIGIR BUGS DE VOLTAR AO SITIO DA MORTE  ##############################################################################################################################################
##############################################################################################################################################
##############################################################################################################################################

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
        global power_up_found

        waiting_for_enemies = False
        run = False
        level_ant = 1
        wait_time = 5
        attack_distance = 3
        count_oneal = 0

        while True:
            try:
                state = json.loads(
                    await websocket.recv()
                )  # receive game state, this must be called timely or your game will get out of sync with the server4

                ######################################################################################################################################
                try:
                    position = state['bomberman']  # Bomberman's position
                    walls = state['walls']  # Walls's position
                    enemies = state['enemies']  # Enemy's position
                    power_ups = state['powerups']  # Power-Ups's position
                    level = state['level']  # Get Level
                    bombs = state['bombs']
                    exit_pos = state['exit']
                except:
                    pass

                if bombs:
                    bomb = bombs[0]
                else:
                    bomb = None

                if level != 1:
                    wait_time = 7

                if len(enemies) == 0:  # Get position of closest enemy
                    pos_enemy = None
                else:
                    pos_enemy = get_enemies(position, enemies)['pos']

                if find_power_up(power_ups) is None:  # Already found power-up?
                    power_up_found = True
                else:
                    print(power_ups)
                    power_up_found = False

                ################################## No Walls ########################################################################
                if len(walls) == 0:  # If walls are all destroyed
                    if put_bomb and not run:  # Set running route
                        run_to = run_away(mapa, position, enemies, walls, bomb, pos_enemy)
                        wait = 0
                        run = True

                    if put_bomb:  # Run from bomb and wait for explosion
                        if position == run_to and wait < 4:
                            wait += 1
                            key = ""
                        elif position == run_to:
                            put_bomb = False
                            run = False
                        key = astar_path(mapa.map, position, run_to, True, enemies)

                        if pos_enemy is not None:
                            if calc_distance(position, pos_enemy) < 3 and not put_bomb and on_same_line(position,
                                                                                                        pos_enemy,
                                                                                                        mapa):
                                key = attack()

                    if len(enemies) != 0:  # If there are still enemies
                        if has_Ballooms(enemies):
                            if not put_bomb and position != [1, 1]:  # If power-up is found
                                key = astar_path(mapa.map, position, [1, 1], True, enemies)
                            elif position == [1, 1] and calc_distance(position, pos_enemy) > 3 and not put_bomb:
                                waiting_for_enemies = True
                            elif calc_distance(position, pos_enemy) < 4 and not put_bomb and on_same_line(position,
                                                                                                          pos_enemy,
                                                                                                          mapa):
                                key = attack()
                        else:
                            attack_distance = 3
                            key = astar_path(mapa.map, position, pos_enemy, True, enemies)
                            if calc_distance(position, pos_enemy) < attack_distance and not put_bomb and on_same_line(
                                    position, pos_enemy, mapa):
                                key = attack()
                    else:  # If enemies are all dead
                        key = astar_path(mapa.map, position, exit_pos, True, enemies)  # Go to exit

                ###############################################################################################################
                ############################################### With Walls ####################################################
                else:  # If walls exist    

                    wall_closer = get_walls(position, mapa, walls)  # Get closer wall
                    key = astar_path(mapa.map, position, wall_closer, False, enemies)  # walk to the closest wall

                    if put_bomb and not run:  # Set running route
                        run_to = run_away(mapa, position, enemies, walls, bomb, pos_enemy)
                        wait = 0
                        run = True

                    print(run)
                    if put_bomb and run:  # Run from bomb and wait for explosion
                        key = astar_path(mapa.map, position, run_to, True, enemies)
                        if position == [1, 1]:
                            run = False
                            put_bomb = False
                        if position == run_to and wait < wait_time:
                            wait += 1
                            key = ""
                            print("Wait")
                        elif position == run_to:
                            put_bomb = False
                            run = False

                    if has_Oneals(enemies) and not put_bomb:
                        attack_distance = 4
                        key = astar_path(mapa.map, position, find_Oneal(position, enemies)['pos'], True, enemies)
                        if calc_distance(position, find_Oneal(position, enemies)['pos']) <= 5:
                            count_oneal += 1
                        if count_oneal == 10:
                            print("Leave Oneal")
                            key = astar_path(mapa.map, position, wall_closer, False, enemies)
                            count_oneal = 0

                    if calc_distance(position, wall_closer) == 1 and not put_bomb:  # attack a wall
                        print("Attack parede! ")
                        key = attack()

                ####################################################################################################################
                ############################################ WITH OR WITHOUT WALLS #################################################

                if not put_bomb and not power_up_found:  # if bomb is not planted and power-up not found yet
                    key = astar_path(mapa.map, position, find_power_up(power_ups), True, enemies)  # Get power-up
                    level = 2

                if pos_enemy is not None:
                    if calc_distance(position, pos_enemy) < attack_distance and not put_bomb and on_same_line(position,
                                                                                                              pos_enemy,
                                                                                                              mapa):
                        key = attack()

                if key is None or waiting_for_enemies:  # Ficar parado
                    if key is None:
                        key = ""

                print("key: ", key)

                if level != level_ant:
                    direction = True
                    put_bomb = False
                    wait = 0
                    power_up_found = False
                    waiting_for_enemies = False
                    run = False
                    wait_time = 6

                level_ant = level

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


def on_same_line(pos, dest, mapa):
    x, y = pos
    dx, dy = dest
    if x == dx and not wall_blocking(pos, dest, mapa):
        return True
    if y == dy and not wall_blocking(pos, dest, mapa):
        return True

    return False


def wall_blocking(pos, dest, mapa):
    x, y = pos
    dx, dy = dest

    if x == dx:
        for i in range(y, dy):
            if mapa.map[x][i] == 1:
                return True
    elif y == dy:
        for i in range(x, dx):
            if mapa.map[i][y] == 1:
                return True

    return False


def astar_path(mapa, pos, destiny, close, enemies):
    if pos == destiny:
        return ""
    path = astar.astar(mapa, pos, destiny, [x['pos'] for x in enemies])
    if (len(path) <= 1 and close) or path is None:
        return walk(pos, destiny)
    elif len(path) <= 1 or has_enemy(path[1], enemies) or len(path) >= 3 and has_enemy(path[2], enemies):
        return ""

    return walk(path[0], path[1])


def has_Ballooms(enemies):
    for enemy in enemies:
        if enemy['name'] == "Balloom":
            return True
    return False


def has_Oneals(enemies):
    for enemy in enemies:
        if enemy['name'] == "Oneal":
            return True
    return False


def find_Oneal(position, enemies):
    min = 10000
    if len(enemies) != 0:
        for enemy in enemies:
            if enemy['name'] == "Oneal":
                if calc_distance(position, enemy['pos']) < min:
                    min = calc_distance(position, enemy['pos'])
                    enemy_closer = enemy
    else:
        enemy_closer = None
    return enemy_closer


def run_away(mapa, pos, enemies, walls, bomb, close_enemy):
    if is_between_walls(mapa, pos):
        # Foge de uma maneira
        return bw_is_safe(mapa, pos, enemies, walls, bomb, close_enemy)
    elif not is_between_walls(mapa, pos):
        # Foge de outra maneira
        return not_bw_is_safe(mapa, pos, enemies, walls, bomb, close_enemy)
    return pos


def bw_is_safe(mapa, pos, enemies, walls, bomb, close_enemy):
    x, y = pos

    if not has_enemy((x + 1, y), enemies) and mapa.map[x + 1][y] == 0 and [x + 1, y] not in walls:
        if not has_enemy((x + 1, y + 1), enemies) and mapa.map[x + 1][y + 1] == 0 and [x + 1, y + 1] not in walls:
            # if not in_range((x + 1,y + 1),bomb,mapa):
            # if calc_distance((x + 1,y + 1),close_enemy) > 3:
            return [x + 1, y + 1]
        elif not has_enemy((x + 1, y - 1), enemies) and mapa.map[x + 1][y - 1] == 0 and [x + 1, y - 1] not in walls:
            # if not in_range((x + 1,y - 1),bomb,mapa):
            # if calc_distance((x + 1,y - 1),close_enemy) > 3:
            return [x + 1, y - 1]

    elif not has_enemy((x - 1, y), enemies) and mapa.map[x - 1][y] == 0 and [x - 1, y] not in walls:
        if not has_enemy((x - 1, y + 1), enemies) and mapa.map[x - 1][y + 1] == 0 and [x - 1, y + 1] not in walls:
            # if not in_range((x - 1,y + 1),bomb,mapa):
            # if calc_distance((x-1,y+1),close_enemy) > 3:
            return [x - 1, y + 1]
        elif not has_enemy((x - 1, y - 1), enemies) and mapa.map[x - 1][y - 1] == 0 and [x - 1, y - 1] not in walls:
            # if not in_range((x - 1,y - 1),bomb,mapa):
            # if calc_distance((x-1,y-1),close_enemy) > 3:
            return [x - 1, y - 1]

    ##################################################################################################################
    if not has_enemy((x, y + 1), enemies) and mapa.map[x][y + 1] == 0 and [x, y + 1] not in walls:
        if not has_enemy((x + 1, y + 1), enemies) and mapa.map[x + 1][y + 1] == 0 and [x + 1, y + 1] not in walls:
            if not has_enemy((x + 2, y + 1), enemies) and mapa.map[x + 2][y + 1] == 0 and [x + 2, y + 1] not in walls:
                # if not in_range((x + 2,y + 1),bomb,mapa):
                # if calc_distance((x+2,y+1),close_enemy) > 3:
                return [x + 2, y + 1]
        elif not has_enemy((x - 1, y + 1), enemies) and mapa.map[x - 1][y + 1] == 0 and [x - 1, y + 1] not in walls:
            if not has_enemy((x - 2, y + 1), enemies) and mapa.map[x - 2][y + 1] == 0 and [x - 2, y + 1] not in walls:
                # if not in_range((x - 2,y + 1),bomb,mapa):
                # if calc_distance((x-2,y+1),close_enemy) > 3:
                return [x - 2, y + 1]

    elif not has_enemy((x, y - 1), enemies) and mapa.map[x][y - 1] == 0 and [x, y - 1] not in walls:
        if not has_enemy((x + 1, y - 1), enemies) and mapa.map[x + 1][y - 1] == 0 and [x + 1, y - 1] not in walls:
            if not has_enemy((x + 2, y - 1), enemies) and mapa.map[x + 2][y - 1] == 0 and [x + 2, y - 1] not in walls:
                # if not in_range((x + 2,y - 1),bomb,mapa):
                # if calc_distance((x+2,y-1),close_enemy) > 3:
                return [x + 2, y - 1]
        elif not has_enemy((x - 1, y - 1), enemies) and mapa.map[x - 1][y - 1] == 0 and [x - 1, y - 1] not in walls:
            if not has_enemy((x - 2, y - 1), enemies) and mapa.map[x - 2][y - 1] == 0 and [x - 2, y - 1] not in walls:
                # if not in_range((x - 2,y - 1),bomb,mapa):
                # if calc_distance((x-2,y-1),close_enemy) > 3:
                return [x - 2, y - 1]
    return pos


def not_bw_is_safe(mapa, pos, enemies, walls, bomb, close_enemy):
    x, y = pos

    if not has_enemy((x, y + 1), enemies) and mapa.map[x][y + 1] == 0 and [x, y + 1] not in walls:
        if not has_enemy((x, y + 2), enemies) and mapa.map[x][y + 2] == 0 and [x, y + 2] not in walls:
            if not has_enemy((x + 1, y + 2), enemies) and mapa.map[x + 1][y + 2] == 0 and [x + 1, y + 2] not in walls:
                # if not in_range((x + 1,y + 2),bomb,mapa):
                # if calc_distance((x+1,y+2),close_enemy) > 3:
                return [x + 1, y + 2]
            elif not has_enemy((x - 1, y + 2), enemies) and mapa.map[x - 1][y + 2] == 0 and [x - 1, y + 2] not in walls:
                # if not in_range((x - 1,y + 2),bomb,mapa):
                # if calc_distance((x-1,y+2),close_enemy) > 3:
                return [x - 1, y + 2]

    if not has_enemy((x, y - 1), enemies) and mapa.map[x][y - 1] == 0 and [x, y - 1] not in walls:
        if not has_enemy((x, y - 2), enemies) and mapa.map[x][y - 2] == 0 and [x, y - 2] not in walls:
            if not has_enemy((x + 1, y - 2), enemies) and mapa.map[x + 1][y - 2] == 0 and [x + 1, y - 2] not in walls:
                # if not in_range((x + 1,y - 2),bomb,mapa):
                # if calc_distance((x+1,y-2),close_enemy) > 3:
                return [x + 1, y - 2]
            elif not has_enemy((x - 1, y - 2), enemies) and mapa.map[x - 1][y - 2] == 0 and [x - 1, y - 2] not in walls:
                # if not in_range((x - 1,y - 2),bomb,mapa):
                # if calc_distance((x-1,y-2),close_enemy) > 3:
                return [x - 1, y - 2]

    if not has_enemy((x + 1, y), enemies) and mapa.map[x + 1][y] == 0 and [x + 1, y] not in walls:
        if not has_enemy((x + 2, y), enemies) and mapa.map[x + 2][y] == 0 and [x + 2, y] not in walls:
            if not has_enemy((x + 2, y + 1), enemies) and mapa.map[x + 2][y + 1] == 0 and [x + 2, y + 1] not in walls:
                # if not in_range((x + 2,y + 1),bomb,mapa):
                # if calc_distance((x+2,y+1),close_enemy) > 3:
                return [x + 2, y + 1]
            elif not has_enemy((x + 2, y - 1), enemies) and mapa.map[x + 2][y - 1] == 0 and [x + 2, y - 1] not in walls:
                # if not in_range((x + 2,y - 1),bomb,mapa):
                # if calc_distance((x+2,y-1),close_enemy) > 3:
                return [x + 2, y - 1]

    if not has_enemy((x - 1, y), enemies) and mapa.map[x - 1][y] == 0 and [x - 1, y] not in walls:
        if not has_enemy((x - 2, y), enemies) and mapa.map[x - 2][y] == 0 and [x - 2, y] not in walls:
            if not has_enemy((x - 2, y + 1), enemies) and mapa.map[x - 2][y + 1] == 0 and [x - 2, y + 1] not in walls:
                # if not in_range((x - 2,y + 1),bomb,mapa):
                # if calc_distance((x-2,y+1),close_enemy) > :
                return [x - 2, y + 1]
            elif not has_enemy((x - 2, y - 1), enemies) and mapa.map[x - 2][y - 1] == 0 and [x - 2, y - 1] not in walls:
                # if not in_range((x - 2,y - 1),bomb,mapa):
                # if calc_distance((x-2,y-1),close_enemy) > 2:
                return [x - 2, y - 1]

    return pos


def is_between_walls(mapa, pos):
    x, y = pos
    if mapa.is_stone((x, y + 1)) and mapa.is_stone((x, y - 1)) or mapa.is_stone((x + 1, y)) and mapa.is_stone(
            (x - 1, y)):
        return True
    return False


def has_enemy(location, enemies):
    x, y = location
    for enemy in enemies:
        enemy = tuple(enemy['pos'])
        if (x, y) == enemy or (x + 1, y) == enemy or (x - 1, y - 1) == enemy or (x, y - 1) == enemy or (
                x - 1, y - 1) == enemy or (x - 1, y) == enemy or (x - 1, y + 1) == enemy or (x, y + 1) == enemy or (
                x + 1, y + 1) == enemy:
            return True
    return False


def find_power_up(power_ups):
    for power in power_ups:
        return power[0]


def attack():
    global put_bomb
    put_bomb = True
    return "B"


def calc_distance(pos1, pos2):
    x1, y1 = pos1
    x2, y2 = pos2
    return math.sqrt(pow(x2 - x1, 2) + pow(y2 - y1, 2))


def walk(pos1, pos2):
    x, y = pos1
    x_2, y_2 = pos2

    if x < x_2:
        return "d"
    if x > x_2:
        return "a"
    if y > y_2:
        return "w"
    if y < y_2:
        return "s"


def reverse(path):
    reversed_path = []
    for key in path:
        if key == "a":
            reversed_path.append("d")
        if key == "d":
            reversed_path.append("a")
        if key == "w":
            reversed_path.append("s")
        if key == "s":
            reversed_path.append("w")
    return reversed_path


def get_walls(position, mapa, walls):
    min = 10000
    wall_len = len(walls)
    if wall_len != 0:
        for wall in walls:
            if not mapa.is_stone(wall):
                if calc_distance(position, wall) < min:
                    min = calc_distance(position, wall)
                    wall_closer = wall
        return wall_closer


# def in_range(character,bomb,mapa):
#         bx, by = bomb[0]
#         x,y = character
#         if mapa.is_stone((x,y)):
#             print("###########################################################################################################")
#             return False
#         if by == y:
#             for r in range(bomb[2] + 1):
#                 if mapa.is_stone((bx + r, by)):
#                     break  # protected by stone to the right
#                 if (x, y) == (bx + r, by):
#                     print("###########################################################################################################")
#                     return True
#             for r in range(bomb[2] + 1):
#                 if mapa.is_stone((bx - r, by)):
#                     break  # protected by stone to the left 
#                 if (x, y) == (bx - r, by):
#                     print("###########################################################################################################")
#                     return True
#         if bx == x:
#             for r in range(bomb[2] + 1):
#                 if mapa.is_stone((bx, by + r)):
#                     break  # protected by stone in the bottom
#                 if (x, y) == (bx, by + r):
#                     print("###########################################################################################################")
#                     return True
#             for r in range(bomb[2] + 1):
#                 if mapa.is_stone((bx, by - r)):
#                     break  # protected by stone in the top
#                 if (x, y) == (bx, by - r):
#                     print("###########################################################################################################")
#                     return True

#         print("Estas livre")
#         return False

def get_enemies(position, enemies):
    min = 10000
    if len(enemies) != 0:
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
