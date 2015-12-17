#!/usr/local/bin/python
import sys
import socket
import select
import struct 
import logging
from datetime import timedelta, datetime
from collections import defaultdict

class node:
	def __init__(self, IP, port):
		self.IP = IP
		self.port = port

neighbors = []
dead_neighbors = []
neighbor_cost = {}
neighbor_init_cost = {}
neighbor_last_recv = {}
my_port = 0
my_IP = ''
timeout = 1
TICK = 1


header_struct = struct.Struct('15s H f')
# recv_port_number(H, 2B). command(s). IP(s). Port(H). dist(f)
update_struct = struct.Struct('H 10s 15s H f')
dv = defaultdict(dict)
first_hop = defaultdict(dict)

#http://stackoverflow.com/questions/24196932/how-can-i-get-the-ip-address-of-eth0-in-python

def get_ip_address():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(("8.8.8.8", 80))
	return s.getsockname()[0]  

def make_header(IP, port, dist):
	values = (IP, port, dist)
	return header_struct.pack(*values)


def make_update_pkt(recv_port, cmd, IP, remote_port, dist):
	values = (recv_port, cmd, IP, remote_port, dist)
	return update_struct.pack(*values)

def add_neighbor(IP, port, dist):
	if (IP, port) not in neighbors:
		logging.debug('add %s %d'% (IP, port))
		neighbors.append((IP, port))	
		neighbor_init_cost[(IP, port)] = dist
	neighbor_cost[(IP, port)] = dist

def showrt():
	logging.debug("neighbor cost original")
	#print_dv()
	'''
	for key in neighbor_init_cost:
		print key, neighbor_init_cost[key]
	'''

	for node in dv[(my_IP, my_port)]:
		IP = node[0]
		port = node[1]
		if IP == my_IP and port == my_port:
			continue
		dist = dv[(my_IP, my_port)][node]
		print 'Destination = ', IP, ':', port, ', Cost = ', dist, ', Link = (', my_IP, ':', my_port, ')'

def handle_input(argv):
	argc = len(argv)
	if argc % 3 != 0:
		print 'Usage: ./bfclient.py localport timeout [ipaddress1 port1 weight1 ...]'
		sys.exit()
	arg_idx = 1
	myport = int(argv[arg_idx])
	arg_idx += 1
	timeout = int(argv[arg_idx])
	arg_idx += 1

	dv[(my_IP, myport)][(my_IP, myport)] = 0
	while arg_idx < argc:
		IP = argv[arg_idx]
		port = int(argv[arg_idx+1])
		dist = float(argv[arg_idx+2])

		add_neighbor(IP, port, dist)

		dv[(my_IP, myport)][(IP, port)] = dist
		arg_idx += 3
	logging.debug('input')
	logging.debug(dv)
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

def make_update_pkts(dst_IP, dst_port):
	pkt =''
	for node in dv[my_node]:
		IP = node[0]
		port = node[1]
		dist = dv[my_node][node]
		# if the packet receiver is the first hop
		if my_node in first_hop:
			if node in first_hop[my_node]:
				if first_hop[my_node][node] == (dst_IP, dst_port):
					dist = float('inf')
					logging.debug('send from %d. To %d: %f' % (my_port, port, dist))
		tmp_pkt = make_update_pkt(my_port, "UPDATE", IP, port, dist)
		pkt += tmp_pkt
	return pkt

# Send my information to other nodes
def route_update(send_socket):
	for IP, port in neighbors:
		payload = make_update_pkts(IP, port)
		header = make_header(my_IP, my_port, neighbor_cost[(IP, port)]) 
		pkt = header+payload
		send_socket.sendto(pkt, (IP, port));

def handle_pkt(d, src_IP):
	idx = 0
	data_len = len(d)
	if data_len == 0:
		return

	idx = header_struct.size
	header = d[0:idx]
	(src_IP, src_port, dist) = header_struct.unpack(header)
	src_IP = src_IP.rstrip('\0')
	add_neighbor(src_IP, src_port, dist)
	neighbor_last_recv[(src_IP, src_port)] = datetime.now()

	while idx < data_len:
		data = d[idx:idx+36]
		idx += 36
		(src_port, cmd, dst_IP, dst_port, dist) = update_struct.unpack(data)
		dst_IP = dst_IP.rstrip('\0')
		logging.debug('received from %d: To %s %d: %f '% (src_port, dst_IP, dst_port, dist))
		src_node = (src_IP, src_port)
		dst_node = (dst_IP, dst_port)
		dv[src_node][dst_node] = dist
		if dst_node not in dv[my_node]: # Add column in dv table
			dv[my_node][dst_node] = float('inf')

def print_dv():
	print 'dv start'
	for a in dv:
		print a, dv[a]
	print 'dv end'

def calc_dv():
	need_update = 0
	for target in dv[my_node]:
		if target == my_node: # Do not calc cost to myself
			continue
		init_value = dv[my_node][target]
		dv[my_node][target] = neighbor_cost.get(target, float('inf'))
		#print target 
		logging.debug(target)
		logging.debug('neighbor_cost: %f' % dv[my_node][target])
		for neighbor in neighbors:
			if neighbor == target:
				continue
			cost = neighbor_cost[neighbor]
			#print_dv()
			logging.debug('first_hop cost %f'% cost)
			cost += dv[neighbor].get (target, float('inf'))
			logging.debug('total cost %f' % cost)
			if cost < dv[my_node][target]:
				dv[my_node][target] = cost
				first_hop[my_node][target] = neighbor
		if init_value != dv[my_node][target]:
			logging.debug("init: %f changed: %f" % (init_value, dv[my_node][target]))
			need_update = 1
	return need_update

def linkup(IP, port):

	if (IP, port) not in neighbors:
		print IP, port, 'is not my neighbor'
		logging.debug(neighbors)
		return

	need_notify = 0
	if neighbor_cost[(IP, port)] != neighbor_init_cost[(IP, port)]:
		neighbor_cost[(IP, port)] = neighbor_init_cost[(IP, port)]
		need_notify = 1
	need_notify |= calc_dv()
	if need_notify:
		route_update(send_socket)
	
def linkdown(IP, port):

	if (IP, port) not in neighbors:
		print IP, port, 'is not my neighbor'
		logging.debug(neighbors)
		return

	need_notify = 0
	if neighbor_cost[(IP, port)]  != float('inf'):
		neighbor_cost[(IP, port)] = float('inf') 
		need_notify = 1
	need_notify |= calc_dv()
	if need_notify:
		route_update(send_socket)

def parse_cmd(msg):
	if msg == "":
		return

	sp = msg.split()
	if sp[0] == "SHOWRT" or sp[0] == "s":
		if len(sp) == 1:
			showrt()
			return
	elif sp[0] == "LINKDOWN" or sp[0] == 'd':
		if len(sp) == 3:
			linkdown(sp[1], int(sp[2]))
			return

	elif sp[0] == "LINKUP" or sp[0] == 'u':
		if len(sp) == 3:
			linkup(sp[1], int(sp[2]))
			return
	elif sp[0] == "CLOSE" or sp[0] == 'c':
		if len(sp) == 1:
			sys.exit()
			return

	print 'invalid command: ', msg

def execute_cmd(msg):
	parse_cmd(msg)
	return 0

def check_neighbor_timeout():
	for neighbor in neighbor_last_recv:
		if datetime.now() - neighbor_last_recv[neighbor] > timedelta(seconds=timeout*3):
			dead_neighbors.append(neighbor)

	for neighbor in dead_neighbors:
		if neighbor in neighbor_last_recv:
			neighbors.remove(neighbor)
			del neighbor_last_recv[neighbor]
			del neighbor_cost[neighbor]
			del neighbor_init_cost[neighbor]

def main():
#	logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(message)s')
	logging.debug('This is debug %s' % "abc")
	global my_port, my_IP, my_node, send_socket
	my_IP = get_ip_address()
	my_port = handle_input(sys.argv)
	my_node = (my_IP, my_port)
	recv_socket = init_socket(0)
	send_socket = init_socket(1)
	route_update(send_socket)
	last_route = datetime.now()

	socket_list = [sys.stdin, recv_socket]
	while 1:
		read_sockets, write_sockets, error_sockets = select.select(socket_list , [], [], TICK)
		if read_sockets:
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
					execute_cmd(msg)
		if datetime.now() - last_route > timedelta(seconds=timeout):
			route_update(send_socket)
			last_route = datetime.now()
		check_neighbor_timeout()

if __name__ == '__main__':
	main()
