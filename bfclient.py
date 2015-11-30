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

def add_neighbor(IP, port):
	x = node(IP, port)
	if (IP, port) not in neighbors:
		print 'add ', IP, port
		neighbors.append((IP, port))	

def showrt():
	print dv
	for node in dv[(my_IP, my_port)]:
		IP = node[0]
		port = node[1]
		dist = dv[(my_IP, my_port)][node]
		print 'Destination = ', IP, ', Cost = ', dist, ', Link = (', IP, ':', port, ')'

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
		print 'received', dst_IP, dst_port, dist
		dst_IP = dst_IP.rstrip('\0')
		dv[(src_IP, src_port)][(dst_IP, dst_port)] = dist
		if (dst_IP, dst_port) not in dv[(my_IP, my_port)]:
			if dst_IP == my_IP and dst_port == my_port:
				dv[(my_IP, my_port)][(src_IP, src_port)] = dist #TODO is this right way to initialize?
			else:
				dv[(my_IP, my_port)][(dst_IP, dst_port)] = 100 #TODO calc distance
	add_neighbor(src_IP, src_port)

def main():
	global my_port, my_IP
	my_IP = get_ip_address()
	my_port = handle_input(sys.argv)
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
				'''
				update_dv()	
				need_notify = calc_dv()
				if need_notify:
					send_dv()
				'''
			#user entered a message
			else :
				msg = raw_input()
				showrt()
				route_update(send_socket)


if __name__ == '__main__':
	main()
