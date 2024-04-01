import websockets
from websockets.sync.server import ServerConnection,WebSocketServer
from websockets import ConnectionClosedOK
from threading import Thread,Lock
import json

connections:dict = {} # stores the list of currently connected clients
websocket_server:WebSocketServer = None # holds the websocket server
con_lock:Lock = Lock() # used for blocking access to the connections dictionary, because more than one thread will try to access it

def remove_connection(sc:ServerConnection):
    global con_lock
    con_lock.acquire()

    global connections
    sc_id = str(sc.id.int)
    if sc_id in connections.keys():
        connections.pop(sc_id)

    con_lock.release()
  
def send(sc:ServerConnection,message:str):
    sc.send(message)

def receive(sc:ServerConnection):
    global connections
    while True: # this loop will exit if the shutdown event is triggered
        try:
            message = sc.recv() # this will block the thread without a timout being set

            # message deserialization
            message:dict = json.loads(message)
            client_id = message["client_id"]
            message = message["message"]
            message:str = f"{client_id}: {message}"

            # broadcast message to all connected clients
            echo(message)

        except ConnectionClosedOK:
            print("receive(): connection closed ok")
            remove_connection(sc)
            break
        except:
            print("receive(): connection closed on error")
            remove_connection(sc)
            break
            

    print("receive(): shutting down")

# this will echo the message to the clients
def echo(message:str):
    print(message)
    global connections
    for sc in connections.values():
        # send the message back to the client with a thread (that way the next send is not waiting for the previous send to finish)
        send_thread = Thread(target=send,args=(sc,message,))
        send_thread.start()

def websocket_handler(sc:ServerConnection):
    print("websocket_handler(): client connected")

    global con_lock
    con_lock.acquire()
    # save the connection to the connections list for broadcasting
    global connections
    connections[str(sc.id.int)] = sc
    con_lock.release()

    receive(sc)

def shutdown_server():

    global con_lock
    con_lock.acquire()

    global connections
    for sc in connections.keys():
        connections[sc].close()

    con_lock.release()

    global websocket_server
    websocket_server.shutdown() # shutdown the websocket server

def input_activity():
    
    while True:

        command = input()
        if command == "-shutdown":
            shutdown_server()
            break

    print("input_activity(): shutting down")
        

def main():
    ia_thread = Thread(target=input_activity)
    ia_thread.start()

    global websocket_server
    websocket_server = websockets.sync.server.serve(websocket_handler,host="localhost",port=8765)
    print("Websocket server started on ws://localhost:8765")
    websocket_server.serve_forever()

    print("main(): server has shutdown")

if __name__ == "__main__":
    main()