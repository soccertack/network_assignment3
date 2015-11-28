#!/usr/local/bin/python
import sys
import socket
import select
import struct 
from collections import defaultdict

class node:
	def __init__(self, IP, port, dist):
		self.IP = IP
		self.port = port
		self.dist = dist

HOST = 'localhost'
neighbors = []
# recv_port_number(H, 2B). command(s). IP(s). Port(H). dist(f)
update_struct = struct.Struct('H 10s 15s H f')
dv = defaultdict(dict)

def make_update_pkt(recv_port, cmd, IP, remote_port, dist):
	values = (recv_port, cmd, IP, remote_port, dist)
	print "make_update_pkt ", IP
	tmp = update_struct.pack(*values)
	print update_struct.unpack(tmp)
	return update_struct.pack(*values)

def handle_input(argv):
	argc = len(argv)
	if argc % 3 != 2:
		print 'Usage:'
		sys.exit()
	arg_idx = 2 # process from the second argument
	while arg_idx < argc:
		IP = argv[arg_idx]
		port = argv[arg_idx+1]
		dist = float(argv[arg_idx+2])
		x = node(argv[arg_idx], int(argv[arg_idx+1]), float(argv[arg_idx+2]))
		neighbors.append(x)	
		dv[('localhost', argv[1])][(IP, port)] = dist
		arg_idx += 3
	return int(argv[1])

def init_socket(myport):
	try :
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	except socket.error, msg :
		print 'Socket creation Fail. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
		sys.exit()
	if myport == 0:
		return s

	try:
		s.bind((HOST, myport))
	except socket.error , msg:
		print 'Bind Fail. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
		sys.exit()
	return s

def main():
	myport = handle_input(sys.argv)
	recv_socket = init_socket(myport)
	send_socket = init_socket(0)

	# Send my information to other nodes
	for neighbor in neighbors:
		# this should be the another loop to send all neighbor data to all neighbors
		pkt = make_update_pkt(myport, "UPDATE", neighbor.IP, neighbor.port, neighbor.dist)
		send_socket.sendto(pkt, (neighbor.IP, neighbor.port));

	socket_list = [sys.stdin, recv_socket]
	while 1:
		read_sockets, write_sockets, error_sockets = select.select(socket_list , [], [])
		for sock in read_sockets:
			#incoming message from remote server
			if sock == recv_socket:
				print "recv?"
				d = recv_socket.recvfrom(1024)
				(recv_port, cmd, IP, remote_port, dist) = update_struct.unpack(d[0])
				print recv_port ,cmd, IP, remote_port, dist
				IP = IP.rstrip('\0')
				x = node(IP, recv_port, dist)
				neighbors.append(x)	
				dv[('localhost',myport)][(IP, recv_port)] = dist
				
			#user entered a message
			else :
				print "My table"
				print dv
				msg = raw_input()
				for neighbor in neighbors:
					#send_socket.sendto("bcast", (neighbor.IP, neighbor.port));
					print 'send to ', neighbor.IP, neighbor.port, neighbor.dist


if __name__ == '__main__':
	main()
