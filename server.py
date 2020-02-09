import random
import socket
import time
from _thread import *
import threading
from datetime import datetime
import json

clients_lock = threading.Lock()
connected = 0

clients = {}
nextXPos = 0

def connectionLoop(sock):
   while True:
      data, addr = sock.recvfrom(1024)
      data = str(data)
      if addr in clients:
         if 'heartbeat' in data:
            clients[addr]['lastBeat'] = datetime.now()
         elif 'cube_position' in data:
            positionMessage = data[2:-1]
            positionData = json.JSONDecoder().decode(positionMessage)
            clients[addr]['position'] = positionData['position']
         elif 'cube_rotation' in data:
            rotationMessage = data[2:-1]
            rotationData = json.JSONDecoder().decode(rotationMessage)
            clients[addr]['rotation'] = rotationData['rotation']
      else:
         if 'connect' in data:
            # Inform existing players of the new player:
            print("Player {} joined.".format(addr));
            clients[addr] = {}
            clients[addr]['lastBeat'] = datetime.now()
            clients[addr]['color'] = 0
            clients[addr]['position'] = {"X": -1, "Y": -1, "Z": -1}
            clients[addr]['rotation'] = {"X": 0, "Y": 0, "Z": 0}
            message = {"cmd": 0, "players":[{"id":str(addr), "color": clients[addr]['color'], "position": clients[addr]['position'], "rotation": clients[addr]['rotation']}]}
            m = json.dumps(message)
            for c in clients:
               if c != addr :
                  sock.sendto(bytes(m,'utf8'), (c[0],c[1]))
               else:
                  message = {"cmd": 4, "players":[{"id":str(addr), "color": clients[addr]['color'], "position": clients[addr]['position'], "rotation": clients[addr]['rotation']}]}
                  m = json.dumps(message)
                  sock.sendto(bytes(m,'utf8'), (c[0],c[1]))
                  
            # To Do: Inform the new player of other players connected to the server:
            otherPlayers = {"cmd": 2, "players": []}
            for c in clients:
               player = {}
               player['id'] = str(c)
               player['color'] = clients[c]['color']
               player['position'] = clients[c]['position']
               player['rotation'] = clients[c]['rotation']
               otherPlayers['players'].append(player)
            sock.sendto(bytes(json.dumps(otherPlayers),'utf8'), (addr[0], addr[1]))
            print("List of players sent to {}".format(addr));

def cleanClients(sock):
   while True:
      for c in list(clients.keys()):
         if (datetime.now() - clients[c]['lastBeat']).total_seconds() > 5:
            print('Dropped Player: ', c)
            playerLeftMessage = {"cmd": 3,"players":[]}
            player = {}
            player['id'] = str(c)
            player['color'] = clients[c]['color']
            player['position'] = clients[c]['position']
            player['rotation'] = clients[c]['rotation']
            playerLeftMessage['players'].append(player)
            clients_lock.acquire()
            del clients[c]
            clients_lock.release()
            # To Do: Inform existing players of the player who left:
            for f in clients:
               sock.sendto(bytes(json.dumps(playerLeftMessage),'utf8'), (f[0],f[1]))
      time.sleep(1)

def gameLoop(sock):
   while True:
      GameState = {"cmd": 1, "players": []}
      clients_lock.acquire()
      #print (clients)
      for c in clients:
         player = {}
         clients[c]['color'] = {"R": random.random(), "G": random.random(), "B": random.random()}
         if clients[c]['position']['Z'] == -1:
            global nextXPos
            player['position'] = {"X": nextXPos, "Y": 0, "Z": 0}
            nextXPos += 2
            clients[c]['position'] = player['position']
         else:
            player['position'] = clients[c]['position']
         player['rotation'] = clients[c]['rotation']
         player['id'] = str(c)
         player['color'] = clients[c]['color']
         GameState['players'].append(player)
      s=json.dumps(GameState)
      #print(s)
      for c in clients:
         sock.sendto(bytes(s,'utf8'), (c[0],c[1]))
      clients_lock.release()
      time.sleep(1)

def main():
   print("Server Started Running")
   port = 12345
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   s.bind(('', port))
   start_new_thread(gameLoop, (s,))
   start_new_thread(connectionLoop, (s,))
   start_new_thread(cleanClients,(s,))
   while True:
      time.sleep(1)

if __name__ == '__main__':
   main()
