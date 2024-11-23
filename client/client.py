import websockets
from websockets.sync.client import ClientConnection
from websockets import ConnectionClosedOK
from threading import Thread,Event,Lock
from queue import Queue,Empty
import json
import sys

SERVER_HOST = "localhost"
SERVER_PORT = 8765

client_id:str = None
outbound_messages:Queue = Queue()

# this thread would be the main activity thread that does something 
def main_activity(cc:ClientConnection,shutdown_event:Event,messages_lock:Lock):
    while not shutdown_event.is_set():
        message = input("") # this will hold the thread here, waiting on cli i/o

        if message == "-exit":
            shutdown_event.set()
            cc.close()
            break

        messages_lock.acquire()

        global outbound_messages

        message = {"client_id":client_id,"message":message}
        message = json.dumps(message)

        outbound_messages.put(item=message,block=False)

        messages_lock.release()
    
    print("main_activity(): shutting down")

def send(cc:ClientConnection,shutdown_event:Event,messages_lock:Lock):

    while not shutdown_event.is_set():
        try:

            messages_lock.acquire()

            global outbound_messages

            # dequeue the pending outbound messages
            while outbound_messages.qsize() > 0:
                try:
                    message = outbound_messages.get(block=False)
                    cc.send(message)
                except Empty: # gets called if the queue was empty when get() was called
                    break # break if the queue was empty

            messages_lock.release()
                
        except ConnectionClosedOK:
            print("send(): connection closed ok")
            shutdown_event.set()
            break
        except:
            print("send(): connection closed on error")
            shutdown_event.set()
            break

    print("send(): shutting down.")

def receive(cc:ClientConnection,shutdown_event:Event):

    while not shutdown_event.is_set(): # break the loop if the client has chosen to exit from the send() thread
        try:
            # this will throw a ConnectionClosedOK error either when the server or the activity_thread closes the socket
            message = cc.recv()
            print(message)
        except ConnectionClosedOK:
            print("receive(): connection closed ok")
            shutdown_event.set()
            break
        except Exception as e:
            print("receive(): connection closed on error. Error -> ",str(e))
            shutdown_event.set()
            break

    print("receive(): shutting down.")
    
def connect():
    uri = f"ws://{SERVER_HOST}:{SERVER_PORT}"

    client_con:ClientConnection = websockets.sync.client.connect(uri=uri)

    # send introduction message
    global client_id
    intro_message:dict = {"client_id":client_id,"message":f"{client_id} connected"}
    intro_message = json.dumps(intro_message)
    client_con.send(intro_message)

    shutdown_event = Event() # used by of the three threads to signal that to the other threads to shutdown
    messages_lock = Lock() # controls access to the messages queue
    
    receive_thread = Thread(target=receive,args=(client_con,shutdown_event,))
    receive_thread.start()

    send_thread = Thread(target=send,args=(client_con,shutdown_event,messages_lock))
    send_thread.start()

    activity_thread = Thread(target=main_activity,args=(client_con,shutdown_event,messages_lock,))
    activity_thread.start()

def parse_cli_arguments(args:list) -> False:

    if(len(args) < 3):
        print("Error. Expecting 2 arguments: <SERVER HOST> <SERVER PORT>")
        return False

    global SERVER_HOST
    global SERVER_PORT

    SERVER_HOST = str(args[1])
    SERVER_PORT = int(args[2])

    return True

def main():

    if(not parse_cli_arguments(sys.argv)):
        return

    global client_id
    client_id = input("Enter your user name: ")

    connect()

if __name__ == "__main__":
    main()