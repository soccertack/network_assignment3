#!/usr/local/bin/python
import sys
import socket
import select
import struct 
from collections import defaultdict

class node:
	def __init__(self, IP, port):
		self.IP = IP
		self.port = port

HOST = ''
neighbors = []

header_struct = struct.Struct('H')
# recv_port_number(H, 2B). command(s). IP(s). Port(H). dist(f)
update_struct = struct.Struct('H 10s 15s H f')
dv = defaultdict(dict)

#http://stackoverflow.com/questions/24196932/how-can-i-get-the-ip-address-of-eth0-in-python

def get_ip_address():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(("8.8.8.8", 80))
	return s.getsockname()[0]  

def make_update_pkt(recv_port, cmd, IP, remote_port, dist):
	values = (recv_port, cmd, IP, remote_port, dist)
	return update_struct.pack(*values)

def add_neighbor(IP, port):
	x = node(IP, port)
	if (IP, port) not in neighbors:
		print 'add ', IP, port
		neighbors.append((IP, port))	

def handle_input(argv):
	argc = len(argv)
	if argc % 3 != 2:
		print 'Usage:'
		sys.exit()
	myport = int(argv[1])
	arg_idx = 2 # process from the second argument
	while arg_idx < argc:
		IP = argv[arg_idx]
		port = int(argv[arg_idx+1])
		dist = float(argv[arg_idx+2])

		add_neighbor(IP, port)

		dv[('localhost', myport)][(IP, port)] = dist
		arg_idx += 3
	return myport

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

def make_mydv(myport):
#	values = (myport)
#	header = header_struct.pack(*values)
	header = ''
	pkt =''
	for node in dv[('localhost', myport)]:
		IP = node[0]
		port = node[1]
		dist = dv[('localhost', myport)][node]
		tmp_pkt = make_update_pkt(myport, "UPDATE", IP, port, dist)
		pkt += tmp_pkt
	return header+pkt

# Send my information to other nodes
def route_update(myport, send_socket):
	pkt = make_mydv(myport)
	for IP, port in neighbors:
		send_socket.sendto(pkt, (IP, port));

def handle_pkt(myport, d, sender_IP):
	idx = 0
	data_len = len(d)

	while idx < data_len:
		data = d[idx:idx+36]
		idx += 36
		(recv_port, cmd, IP, remote_port, dist) = update_struct.unpack(data)
		print recv_port ,cmd, IP, remote_port, dist
		IP = IP.rstrip('\0')
		dv[('localhost',myport)][(IP, recv_port)] = dist

	add_neighbor(sender_IP, recv_port)

def main():
	myport = handle_input(sys.argv)
	recv_socket = init_socket(myport)
	send_socket = init_socket(0)
	route_update(myport, send_socket)

	socket_list = [sys.stdin, recv_socket]
	while 1:
		read_sockets, write_sockets, error_sockets = select.select(socket_list , [], [])
		for sock in read_sockets:
			#incoming message from remote server
			if sock == recv_socket:
				d = recv_socket.recvfrom(1024)
				sender_IP = d[1][0]
				handle_pkt(myport, d[0], sender_IP)
				'''
				update_dv()	
				need_notify = calc_dv()
				if need_notify:
					send_dv()
				'''
			#user entered a message
			else :
				msg = raw_input()
				route_update(myport, send_socket)


if __name__ == '__main__':
	main()
