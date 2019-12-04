import sys
import json
import asyncio
import websockets
import getpass
import os
import math
import astar
import random

from mapa import Map

# Next 2 lines are not needed for AI agent

# pygame.init()

direction = True
put_bomb = False
power_up_reveal = True
way = []


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
        global power_up_reveal
        global way
        wait = 0

        waiting_for_enemies = False
        run = False
        level_ant = 1
        wait_time = 7
        attack_distance = 3
        count_oneal = 0
        power_up_list = []
        POWER_UP = None
        power_up_reveal_before = True
        got_Detonator = False
        power_up_found = False
        count = 0
        pos_ant = None
        suicide = False
        lives_ant = 3
        objectives = []
        wall_closer = None

        while True:
            try:
                state = json.loads(
                    await websocket.recv()
                )  # receive game state, this must be called timely or your game will get out of sync with the server4

                while websocket.messages:
                    state = json.loads(await websocket.recv())

                ######################################################################################################################################
                try:
                    position = state['bomberman']  # Bomberman's position
                    walls = state['walls']  # Walls's position
                    mapa.walls = walls
                    enemies = state['enemies']  # Enemy's position
                    power_ups = state['powerups']  # Power-Ups's position
                    level = state['level']  # Get Level
                    bombs = state['bombs']
                    exit_pos = state['exit']
                    lives = state['lives']

                except:
                    pass

                corner = get_corner(mapa)

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
                    power_up_reveal = True
                else:
                    power_up_reveal = False
                    POWER_UP = power_ups[0]

                if POWER_UP is not None:
                    if POWER_UP[1] == "Detonator":
                        got_Detonator = True

                Detonate = False


                if not power_up_reveal_before and power_up_reveal:
                    power_up_list.append(POWER_UP)
                    power_up_found = True

                x,y = position

                ################################## No Walls ########################################################################
                if len(walls) == 0:  # If walls are all destroyed
                    if put_bomb and not run:  # Set running route
                        run_to = run_away(mapa, position, enemies, walls, bomb, pos_enemy)
                        wait = 0
                        run = True

                    if put_bomb and run:  # Run from bomb and wait for explosion
                        if not way:
                            key = ""
                        else:
                            key = way.pop()
                        if lives_ant != lives:
                            run = False
                            put_bomb = False
                            way = []
                        if position == run_to and wait < wait_time and not got_Detonator:
                            wait += 1
                        elif position == run_to and not got_Detonator:
                            put_bomb = False
                            run = False
                            way = []
                        elif got_Detonator and position == run_to:
                            put_bomb = False
                            run = False
                            way = []
                            Detonate = True

                        key = astar_path(mapa.map, position, run_to, True, enemies, way)

                        if pos_enemy is not None:
                            if calc_distance(position, pos_enemy) < 3 and not put_bomb and on_same_line(position,
                                                                                                        pos_enemy,
                                                                                                        mapa):
                                key = attack()

                    if len(enemies) != 0:  # If there are still enemies
                        if has_DumbEnemies(enemies):
                            if not put_bomb and position != corner:  # If power-up is found
                                key = astar_path(mapa.map, position, corner, True, enemies, way)
                            elif position == corner and calc_distance(position, pos_enemy) > 3 and not put_bomb:
                                waiting_for_enemies = True
                            elif calc_distance(position, pos_enemy) < 4 and not put_bomb and on_same_line(position,
                                                                                                          pos_enemy,
                                                                                                          mapa):
                                key = attack()
                        else:
                            attack_distance = 3
                            key = astar_path(mapa.map, position, pos_enemy, True, enemies, way)
                            if calc_distance(position, pos_enemy) < attack_distance and not put_bomb and on_same_line(
                                    position, pos_enemy, mapa):
                                key = attack()
                    else:  # If enemies are all dead
                        key = astar_path(mapa.map, position, exit_pos, True, enemies, way)  # Go to exit

                ###############################################################################################################
                ############################################### With Walls ####################################################
                else:  # If walls exist

                    if wall_closer not in walls:
                        wall_closer = get_walls(position, mapa, walls)  # Get closer wall

                    key = astar_path(mapa.map, position, wall_closer, False, enemies, way)  # walk to the closest wall

                    if put_bomb and not run:  # Set running route
                        run_to = run_away(mapa, position, enemies, walls, bomb, pos_enemy)
                        wait = 0
                        run = True
                
                    if put_bomb and run:  # Run from bomb and wait for explosion
                        if not way:
                            key = ""
                        else:
                            key = way.pop()
                        if lives_ant != lives:
                            run = False
                            put_bomb = False
                            way = []
                        if position == run_to and wait < wait_time and not got_Detonator:
                            wait += 1
                            key = ""
                        elif position == run_to and not got_Detonator or wait >= wait_time:
                            put_bomb = False
                            run = False
                            # objectives = []
                            way = []
                        elif got_Detonator and position == run_to:
                            put_bomb = False
                            run = False
                            # objectives = []
                            way = []
                            Detonate = True
                        

                    if has_SmartEnemies(enemies) and not put_bomb:
                        attack_distance = 4
                        key = astar_path(mapa.map, position, find_SmartEnemies(position, enemies)['pos'], True, enemies,
                                         way)
                        if calc_distance(position, find_SmartEnemies(position, enemies)['pos']) <= 5:
                            count_oneal += 1
                        if count_oneal >= 100:
                            key = astar_path(mapa.map, position, wall_closer, False, enemies, way)
                            if calc_distance(position, wall_closer) <= 1:
                                count_oneal = 0

                    if power_up_found and len(enemies) == 0 and exit_pos != [] and not run:
                        key = astar_path(mapa.map, position, exit_pos, True, enemies, way)  # Go to exit

                    if is_beside_walls(position,walls) and not put_bomb:  # attack a wall
                        key = attack()

                ####################################################################################################################
                ############################################ WITH OR WITHOUT WALLS #################################################

                power_up_reveal_before = power_up_reveal

                if not put_bomb and not power_up_reveal and not run and not put_bomb:  # if bomb is not planted and power-up not found yet
                    key = astar_path(mapa.map, position, find_power_up(power_ups), True, enemies, way)  # Get power-up
                    wait_time = 7

                if pos_enemy is not None:
                    if calc_distance(position, pos_enemy) < attack_distance and not put_bomb and on_same_line(position,
                                                                                                              pos_enemy,
                                                                                                              mapa):
                        key = attack()

                if power_up_found and len(enemies) == 0 and exit_pos != [] and not run and not walls:
                        key = astar_path(mapa.map, position, exit_pos, True, enemies, way)  # Go to exit

                if key is None or waiting_for_enemies:  # Ficar parado
                    if key is None:
                        key = ""

                if level != level_ant:
                    direction = True
                    put_bomb = False
                    wait = 0
                    power_up_reveal = False
                    waiting_for_enemies = False
                    run = False
                    wait_time = 6
                    power_up_found = False

                level_ant = level

                

                if pos_ant == position and position != corner:
                    count += 1
                else:
                    count = 0

                if count >= 100 and suicide:
                    key = "A"
                    count = 0
                    suicide = False
                elif count >= 100 and got_Detonator:
                    key = attack()
                    suicide = True
                elif count >= 100 and not got_Detonator:
                    key = attack()
                    count = 0
                
                if Detonate:
                    key = "A"

                pos_ant = position
                lives_ant = lives
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

def is_beside_walls(position,walls):

    x,y = position
    if [x+1,y] in walls:
        return True
    elif [x-1,y] in walls:
        return True
    elif [x,y+1] in walls:
        return True
    elif [x,y-1] in walls:
        return True
    
    return False
def get_corner(mapa):
    for x in range(mapa.hor_tiles):
        for y in range(mapa.ver_tiles):
            if not mapa.is_blocked((x, y)):
                return [x, y]

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


def random_key():
    key_list = ["a", "s", "d", "w"]
    return random.choice(key_list)


def astar_path(mapa, pos, destiny, close, enemies, way):
    if pos == destiny:
        return ""
    path = astar.astar(mapa, pos, destiny, [x['pos'] for x in enemies])
    if path is None:
        return random_key()
    else:
        if len(path) <= 1 and close:
            return walk(pos, destiny)
        elif len(path) <= 1 or has_enemy(path[1], enemies) or len(path) >= 3 and has_enemy(path[2], enemies):
            return random_key()

    return walk(path[0], path[1])


def has_DumbEnemies(enemies):
    for enemy in enemies:
        if enemy['name'] == "Balloom" or enemy['name'] == "Doll":
            return True
    return False


def has_SmartEnemies(enemies):
    for enemy in enemies:
        if enemy['name'] == "Oneal" or enemy['name'] == "Minvo" or enemy['name'] == "Kondoria" or enemy[
            'name'] == "Ovapi" or enemy['name'] == "Pass":
            return True
    return False


def find_SmartEnemies(position, enemies):
    min = 10000
    if len(enemies) != 0:
        for enemy in enemies:
            if enemy['name'] == "Oneal" or enemy['name'] == "Minvo" or enemy['name'] == "Kondoria" or enemy[
                'name'] == "Ovapi" or enemy['name'] == "Pass":
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
    global way

    if not has_enemy((x + 1, y), enemies) and not mapa.is_blocked((x+1,y)):
        if not has_enemy((x + 1, y + 1), enemies) and not mapa.is_blocked((x+1,y+1)):
            way.append('s')
            way.append('d')
            return [x + 1, y + 1]
        if not has_enemy((x + 1, y - 1), enemies) and not mapa.is_blocked((x+1,y-1)):
            way.append('w')
            way.append('d')
            return [x + 1, y - 1]

    if not has_enemy((x - 1, y), enemies) and not mapa.is_blocked((x-1,y)):
        if not has_enemy((x - 1, y + 1), enemies) and not mapa.is_blocked((x-1,y+1)):
            way.append('s')
            way.append('a')
            return [x - 1, y + 1]
        if not has_enemy((x - 1, y - 1), enemies) and not mapa.is_blocked((x-1,y-1)):
            way.append('w')
            way.append('a')
            return [x - 1, y - 1]

    ##################################################################################################################
    if not has_enemy((x, y + 1), enemies) and not mapa.is_blocked((x,y+1)):
        if not has_enemy((x + 1, y + 1), enemies) and not mapa.is_blocked((x+1,y+1)):
            way.append('d')
            way.append('s')
            return [x + 1, y + 1]
        if not has_enemy((x - 1, y + 1), enemies) and not mapa.is_blocked((x-1,y+1)):
            way.append('a')
            way.append('s')
            return [x - 1, y + 1]

    if not has_enemy((x, y - 1), enemies) and not mapa.is_blocked((x,y-1)):
        if not has_enemy((x + 1, y - 1), enemies) and not mapa.is_blocked((x+1,y-1)):
            way.append('d')
            way.append('w')
            return [x + 1, y - 1]
        if not has_enemy((x - 1, y - 1), enemies) and not mapa.is_blocked((x-1,y-1)):
            way.append('a')
            way.append('w')
            return [x - 1, y - 1]

    return run_away_2(mapa, pos, enemies, walls, bomb, close_enemy)


def not_bw_is_safe(mapa, pos, enemies, walls, bomb, close_enemy):
    x, y = pos
    global way

    if not has_enemy((x, y + 1), enemies) and not mapa.is_blocked((x,y+1)):
        if not has_enemy((x, y + 2), enemies) and not mapa.is_blocked((x,y+2)):
            if not has_enemy((x + 1, y + 2), enemies) and not mapa.is_blocked((x+1,y+2)):
                way.append('d')
                way.append('s')
                way.append('s')
                return [x + 1, y + 2]
            if not has_enemy((x - 1, y + 2), enemies) and not mapa.is_blocked((x-1,y+2)):
                way.append('a')
                way.append('s')
                way.append('s')
                return [x - 1, y + 2]

    if not has_enemy((x, y - 1), enemies) and not mapa.is_blocked((x,y-1)):
        if not has_enemy((x, y - 2), enemies) and not mapa.is_blocked((x,y-2)):
            if not has_enemy((x + 1, y - 2), enemies) and not mapa.is_blocked((x+1,y-2)):
                way.append('d')
                way.append('w')
                way.append('w')
                return [x + 1, y - 2]
            if not has_enemy((x - 1, y - 2), enemies) and not mapa.is_blocked((x-1,y-2)):
                way.append('a')
                way.append('w')
                way.append('w')
                return [x - 1, y - 2]

    if not has_enemy((x + 1, y), enemies) and not mapa.is_blocked((x+1,y)):
        if not has_enemy((x + 2, y), enemies) and not mapa.is_blocked((x+2,y)):
            if not has_enemy((x + 2, y + 1), enemies) and not mapa.is_blocked((x+2,y+1)):
                way.append('s')
                way.append('d')
                way.append('d')
                return [x + 2, y + 1]
            if not has_enemy((x + 2, y - 1), enemies) and not mapa.is_blocked((x+2,y-1)):
                way.append('w')
                way.append('d')
                way.append('d')
                return [x + 2, y - 1]

    if not has_enemy((x - 1, y), enemies) and not mapa.is_blocked((x-1,y)):
        if not has_enemy((x - 2, y), enemies) and not mapa.is_blocked((x-2,y)):
            if not has_enemy((x - 2, y + 1), enemies) and not mapa.is_blocked((x-2,y+1)):
                way.append('s')
                way.append('a')
                way.append('a')
                return [x - 2, y + 1]
            if not has_enemy((x - 2, y - 1), enemies) and not mapa.is_blocked((x-2,y-1)):
                way.append('w')
                way.append('a')
                way.append('a')
                return [x - 2, y - 1]


    return run_away_2(mapa,pos,enemies,walls,bomb,close_enemy)


########################################### In case the first L doesnt work #############################################################################
def run_away_2(mapa, pos, enemies, walls, bomb, close_enemy):
    if is_between_walls(mapa, pos):
        # Foge de uma maneira
        return bw_is_safe_2(mapa, pos, enemies, walls, bomb, close_enemy)
    elif not is_between_walls(mapa, pos):
        # Foge de outra maneira
        return not_bw_is_safe_2(mapa, pos, enemies, walls, bomb, close_enemy)
    return pos


def bw_is_safe_2(mapa, pos, enemies, walls, bomb, close_enemy):
    x, y = pos
    global way

    if not mapa.is_blocked((x+1,y)):
        if not mapa.is_blocked((x+1,y+1)):
            way.append('s')
            way.append('d')
            return [x + 1, y + 1]
        if not mapa.is_blocked((x+1,y-1)):
            way.append('w')
            way.append('d')
            return [x + 1, y - 1]

    if not mapa.is_blocked((x-1,y)):
        if not mapa.is_blocked((x-1,y+1)):
            way.append('s')
            way.append('a')
            return [x - 1, y + 1]
        if not mapa.is_blocked((x-1,y-1)):
            way.append('w')
            way.append('a')
            return [x - 1, y - 1]

    ##################################################################################################################
    if not mapa.is_blocked((x,y+1)):
        if not mapa.is_blocked((x+1,y+1)):
            way.append('d')
            way.append('s')
            return [x + 1, y + 1]
        if not mapa.is_blocked((x-1,y+1)):
            way.append('a')
            way.append('s')
            return [x - 1, y + 1]

    if not mapa.is_blocked((x,y-1)):
        if not has_enemy((x + 1, y - 1), enemies) and not mapa.is_blocked((x+1,y-1)):
            way.append('d')
            way.append('w')
            return [x + 1, y - 1]
        if not mapa.is_blocked((x-1,y-1)):
            way.append('a')
            way.append('w')
            return [x - 1, y - 1]

    return pos


def not_bw_is_safe_2(mapa, pos, enemies, walls, bomb, close_enemy):
    x, y = pos
    global way

    if not mapa.is_blocked((x,y+1)):
        if not mapa.is_blocked((x,y+2)):
            if not mapa.is_blocked((x+1,y+2)):
                way.append('d')
                way.append('s')
                way.append('s')
                return [x + 1, y + 2]
            if not mapa.is_blocked((x-1,y+2)):
                way.append('a')
                way.append('s')
                way.append('s')
                return [x - 1, y + 2]

    if not mapa.is_blocked((x,y-1)):
        if not mapa.is_blocked((x,y-2)):
            if not mapa.is_blocked((x+1,y-2)):
                way.append('d')
                way.append('w')
                way.append('w')
                return [x + 1, y - 2]
            if not mapa.is_blocked((x-1,y-2)):
                way.append('a')
                way.append('w')
                way.append('w')
                return [x - 1, y - 2]

    if not mapa.is_blocked((x+1,y)):
        if not mapa.is_blocked((x+2,y)):
            if not mapa.is_blocked((x+2,y+1)):
                way.append('s')
                way.append('d')
                way.append('d')
                return [x + 2, y + 1]
            if not mapa.is_blocked((x+2,y-1)):
                way.append('w')
                way.append('d')
                way.append('d')
                return [x + 2, y - 1]

    if not mapa.is_blocked((x-1,y)):
        if not mapa.is_blocked((x-2,y)):
            if not mapa.is_blocked((x-2,y+1)):
                way.append('s')
                way.append('a')
                way.append('a')
                return [x - 2, y + 1]
            if not mapa.is_blocked((x-2,y-1)):
                way.append('w')
                way.append('a')
                way.append('a')
                return [x - 2, y - 1]

    return pos



###################################################### Run_away backup ###############################################################

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
    if pos1 is None or pos2 is None or pos1 == 0 or pos2 == 0:
        return 0
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
