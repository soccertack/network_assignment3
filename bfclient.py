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

neighbors = []
neighbor_cost = {}
my_port = 0
my_IP = ''

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

def add_neighbor(IP, port, dist):
	if (IP, port) not in neighbors:
		print 'add ', IP, port
		neighbors.append((IP, port))	
	neighbor_cost[(IP, port)] = dist

def showrt():
	for node in dv[(my_IP, my_port)]:
		IP = node[0]
		port = node[1]
		if IP == my_IP and port == my_port:
			continue
		dist = dv[(my_IP, my_port)][node]
		print 'Destination = ', IP, ', Cost = ', dist, ', Link = (', IP, ':', port, ')'

def handle_input(argv):
	argc = len(argv)
	if argc % 3 != 2:
		print 'Usage:'
		sys.exit()
	myport = int(argv[1])
	arg_idx = 2 # process from the second argument
	dv[(my_IP, myport)][(my_IP, myport)] = 0
	while arg_idx < argc:
		IP = argv[arg_idx]
		port = int(argv[arg_idx+1])
		dist = float(argv[arg_idx+2])

		add_neighbor(IP, port, dist)

		dv[(my_IP, myport)][(IP, port)] = dist
		arg_idx += 3
	print 'input'
	print dv
	return myport

def init_socket(for_send):
	try :
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	except socket.error, msg :
		print 'Socket creation Fail. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
		sys.exit()
	if for_send:
		return s

	try:
		s.bind(('', my_port))
	except socket.error , msg:
		print 'Bind Fail. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
		sys.exit()
	return s

def make_update_pkts():
	header = ''
	pkt =''
	for node in dv[(my_IP, my_port)]:
		IP = node[0]
		port = node[1]
		dist = dv[(my_IP, my_port)][node]
		tmp_pkt = make_update_pkt(my_port, "UPDATE", IP, port, dist)
		pkt += tmp_pkt
	return header+pkt

# Send my information to other nodes
def route_update(send_socket):
	pkt = make_update_pkts()
	for IP, port in neighbors:
		send_socket.sendto(pkt, (IP, port));

def handle_pkt(d, src_IP):
	idx = 0
	data_len = len(d)

	while idx < data_len:
		data = d[idx:idx+36]
		idx += 36
		(src_port, cmd, dst_IP, dst_port, dist) = update_struct.unpack(data)
		dst_IP = dst_IP.rstrip('\0')
		print 'received', dst_IP, dst_port, dist
		src_node = (src_IP, src_port)
		dst_node = (dst_IP, dst_port)
		dv[src_node][dst_node] = dist
		if dst_node not in dv[my_node]: # Add column in dv table
			dv[my_node][dst_node] = float('inf')
	add_neighbor(src_IP, src_port, dv[src_node][my_node])
	print neighbor_cost

def print_dv():
	print dv
	print 'dv start'
	for a in dv:
		print dv[a]
	print 'dv end'
def calc_dv():
	need_update = 0
	for target in dv[my_node]:
		if target == my_node: # Do not calc cost to myself
			continue
		init_value = dv[my_node][target]
		dv[my_node][target] = neighbor_cost.get(target, float('inf'))
		for first_hop in neighbors:
			if first_hop == target:
				continue
			cost = neighbor_cost[first_hop]
			print_dv()
			print 'first_hop cost', cost
			print target 
			cost += dv[first_hop].get (target, float('inf'))
			print 'total cost', cost
			if cost < dv[my_node][target]:
				dv[my_node][target] = cost
		if init_value != dv[my_node][target]:
			print "should send update" 	#TODO
			need_update = 1
	return need_update


def main():
	global my_port, my_IP, my_node
	my_IP = get_ip_address()
	my_port = handle_input(sys.argv)
	my_node = (my_IP, my_port)
	recv_socket = init_socket(0)
	send_socket = init_socket(1)
	route_update(send_socket)

	socket_list = [sys.stdin, recv_socket]
	while 1:
		read_sockets, write_sockets, error_sockets = select.select(socket_list , [], [])
		for sock in read_sockets:
			#incoming message from remote server
			if sock == recv_socket:
				d = recv_socket.recvfrom(1024)
				sender_IP = d[1][0]
				handle_pkt(d[0], sender_IP)
				need_notify= calc_dv()
				if need_notify:
					route_update(send_socket)
			#user entered a message
			else :
				msg = raw_input()
				showrt()
				#route_update(send_socket)


if __name__ == '__main__':
	main()
