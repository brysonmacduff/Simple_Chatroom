## Description

This is a simple CLI chatroom project that uses TCP sockets. To try it, run the server.py file first, then start another terminal to run client.py. You can start additional client terminals to have more clients in the chatroom.

## Build Instructions

* Note that you must build for Windows from within the Windows OS. Likewise, you must build for Linux within the Linux OS.

### Linux

python3 pyinstaller --onefile client.py
python3 pyinstaller --onefile server.py

### Windows

* python pyinstaller --onefile client.py
* python pyinstaller --onefile server.py

## Run Instructions

* ./server \<SERVER_HOST\> \<SERVER_PORT\>
* ./client \<SERVER_HOST\> \<SERVER_PORT\>


