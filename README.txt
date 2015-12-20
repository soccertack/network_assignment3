1. Usage
 python bfclient.py localport timeout [ipaddress1 port1 weight1 ...]

2. Program Features
 This program supports all the commands provided by programming assignment 3 specification
 This program supports POISONED REVERSE.

3. Communication protocol between bfclients
 The only message between bfclients is ROUTE UPDATE (distance vector).
 This simplifies communication protocal between clients.

 Message consists of two parts: header and payload.
 Header contains sender's IP address, receive port and distance to receiver. (24 bytes total)
 Payload contains sender's distance vector to destination, which contains dest IP, port and distance. (36 bytes per each destination.)
 Header and payload are packed via python struct respectively.

4. Timeout management 
 The client manages timeout of itself (to send route update) and neighbors (to
receive route update). This is done via select function, and the granularity of
timeout is 1 second. This is reasonable granularity considering that all the timeout
value in this (and previous) assignment are in unit of second.

5. Extra features
This program supports 
 - POISONED REVERSE.
 - change of distance between neighbors.
 - shortcut for each commands.

 4.1) POISONED REVERSE.
    When the shortest distance from A to C is via B,
    then A advertises distance from A to C as infinite to B.
 4.2) change of distance between neighbors.
    The cost between two neighbor can be changed dynamically.
    For example, if node A is launched with the distance to node B is 10,
    then if node B is launched with the distance to node A is 20,
    then the distance between two nodes will be the latter value, which is 20.
   
    This is useful when the cost between two nodes is changed,
    then we don't need to restart both of the nodes, but just need to restart one of them.

 4.3) shortcut for each commands
    Here is the list. (The format is <Commmand>:<Shortcut>)
    SHOWRT: s
    LINKDOWN: d
    LINKUP: u
    CLOSE: c
    

