#!/usr/local/bin/python
import sys
import socket

class node:
	def __init__(self, IP, port, dist):
		self.IP = IP
		self.port = port
		self.dist = dist

HOST = 'localhost'
neighbors = []
def handle_input(argv):
	argc = len(argv)
	if argc % 3 != 2:
		print 'Usage:'
		sys.exit()
	arg_idx = 2 # process from the second argument
	while arg_idx < argc:
		x = node(argv[arg_idx], int(argv[arg_idx+1]), float(argv[arg_idx+2]))
		neighbors.append(x)	
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
		send_socket.sendto("test", (neighbor.IP, neighbor.port));
		print 'send to ', neighbor.IP, neighbor.port, neighbor.dist
	
	while 1:
		d = recv_socket.recvfrom(1024)
		data = d[0]
		addr = d[1]
		print data
		print addr

if __name__ == '__main__':
	main()
