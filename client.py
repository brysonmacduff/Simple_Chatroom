import websockets
from websockets.sync.client import ClientConnection
from websockets import ConnectionClosedOK

import threading
from threading import Thread,Event,Lock
from time import sleep
from queue import Queue,Empty
import json

client_id:str = None
outbound_messages:Queue = Queue()

# this thread would be the main activity thread that does something 
def main_activity(con_event:Event,messages_lock:Lock):
    while not con_event.is_set():
        message = input("") # this will hold the thread here, waiting on cli i/o

        if message == "-exit":
            con_event.set()
            break

        messages_lock.acquire()

        global outbound_messages

        message = {"client_id":client_id,"message":message}
        message = json.dumps(message)

        outbound_messages.put(item=message,block=False)

        messages_lock.release()
    
    print("main_activity(): shutting down")

def send(cc:ClientConnection,con_event:Event,messages_lock:Lock):

    try:
        while not con_event.is_set():

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

            sleep(0.1) # relinquish control of the client connection to the receive() thread
        
        cc.close() # when the loop exits, close the connection
            
    except ConnectionClosedOK:
        print("send(): connection closed normally")
        con_event.set()
    except:
        print("send(): connection closed on error")
        con_event.set()

    print("send(): shutting down.")

def receive(cc:ClientConnection,con_event:Event):

    while not con_event.is_set(): # break the loop if the client has chosen to exit from the send() thread
        try:
            message = cc.recv(timeout=0.1)

            print(message)
        except TimeoutError:
            sleep(0.1) # relinquish control of the client connection to the send() thread
        except ConnectionClosedOK:
            print("receive(): connection closed by server")
            con_event.set()
            break
        except Exception as e:
            print("receive(): connection closed on error. Error -> ",str(e))
            con_event.set()
            break

    print("receive(): shutting down.")
    
def connect():
    uri = "ws://localhost:8765"

    client_con:ClientConnection = websockets.sync.client.connect(uri=uri)

    # send introduction message
    global client_id
    intro_message:dict = {"client_id":client_id,"message":f"{client_id} connected"}
    intro_message = json.dumps(intro_message)
    client_con.send(intro_message)

    con_event = Event()
    messages_lock = Lock()
    
    receive_thread = Thread(target=receive,args=(client_con,con_event,))
    receive_thread.start()

    send_thread = Thread(target=send,args=(client_con,con_event,messages_lock))
    send_thread.start()

    activity_thread = Thread(target=main_activity,args=(con_event,messages_lock,))
    activity_thread.start()


def main():

    global client_id
    client_id = input("Enter your user name: ")

    connect()

if __name__ == "__main__":
    main()