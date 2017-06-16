#!/usr/bin/env python
# -*- coding: utf8 -*-
# filename: server_ftp.py

# Author: Tupac
# Date:   2016.11.23
# Useful: This file is a simple ftp server who is write with SocketServer module.

import SocketServer, commands
import time
import sys
import os
import socket


class MyTCPHandler(SocketServer.BaseRequestHandler):

	def handle(self):
		try:
			print('%s is Connected!' % self.client_address[0])
			while True:
				#self.request is the TCP socket connected to the client
				#print("WAITTING  USER  COMMANDS")
				self.data = self.request.recv(1024).strip()
				print "User Command: %s" % self.data
				if not self.data:
					self.logging('DEAD')
					print('%s is Escape!' % self.client_address[0])
					break

				user_input = self.data.split()
				if user_input[0] != 'get' and user_input[0] != 'put' and user_input[0] != 'exit' and user_input[0] != 'ls':
					self.logging('INVALID_INPUT')
					self.request.send("Please input get or put or exit or ls")
					continue
				elif user_input[0] == 'exit':
					self.logging('EXITED')
					print('%s is Exited!' % self.client_address[0])
					break
				elif user_input[0] == 'get':
					get_list = user_input[1:]
					status = self.get(*get_list)
					if status == 'Finished':
						time.sleep(0.002)
						self.request.send('Finished')	
					continue
				elif user_input[0] == 'put':
					while True:
						status = self.put()
						if status == 'Finished':
							break
						elif status == 'Error': 
							continue
				elif user_input[0] == 'ls':
					user_status, result = commands.getstatusoutput('ls')
					if user_status == 0:
						self.request.sendall(result)
					else:
						self.request.sendall("Done")
		except IOError,ex:
			pass
	def get(self,*obj_list):
		file_and_dir_list = []
		dir_list = []
		
		for obj in obj_list:
			status, result = commands.getstatusoutput('ls ' +  obj + ' -d')		
			if status != 0:
				self.request.send('Ready')
				ack = self.request.recv(1024)
				
				if ack == 'Known':
					self.request.send('Error')
				ack = self.request.recv(1024)
				if ack == 'TellMeWhy':
					self.request.send("No Such File %s" % repr(obj))
				get_message = ['GET', repr(obj), ]
				self.logging('FAILED: ' +  "No Such File %s" % repr(obj), *get_message)
				return 'Error'

			if os.path.isdir(obj):
				self.request.send('Ready')
				ack = self.request.recv(1024)
				if ack == 'Known':
					self.request.send(obj + 'dirr')
				ack = self.request.recv(1024)
				if ack == 'DIR_CREAT_SUCCEED':
					get_message = ['GET DIR', obj]
					self.logging('SUCCEED', *get_message)
				file_and_dir_list = os.listdir(obj)
				if len(file_and_dir_list) == 0:
					self.request.send('EMPTY_DIR')
					continue
				else:
					for file_obj in file_and_dir_list:
						obj_path = obj + '/' + file_obj
						if os.path.isdir(obj_path):
							dir_list.append(obj_path)
						else:	
							self.get_file(obj_path)
		

			else:
				self.get_file(obj)
			if len(dir_list) != 0:
				self.get(*dir_list)

		return 'Finished'		

	def get_file(self, obj):
		self.request.send('Ready')
		ack = self.request.recv(1024)
		if ack == 'Known':
			self.request.send(obj + 'file')
		ack = self.request.recv(1024)
		if ack == 'Ready_Write':
			file_size = os.path.getsize(obj)
			if file_size == 0:
				self.request.send('EMPTY_FILE')
			else:
				self.request.send(str(file_size))
				ack = self.request.recv(1024)
				if ack == 'GET_FILE_SIZE':
					with open(obj, 'rb') as f:
						while True:
							data_read = f.read(1024)
							if len(data_read) == 0: break
							self.request.sendall(data_read)
		ack = self.request.recv(1024)
		if ack == 'Write_End':
			get_message = ['GET FILE', repr(obj)]
			self.logging('SUCCEED', *get_message)

	def put(self):
		#print "Waitting file's type!\n"
		ack = self.request.recv(1024)
		#print('ACK IS %s' % ack)
		if ack == 'Finished':
			return 'Finished'
		if ack == 'EMPTY_DIR':
			return 'EMPTY_DIR'
		if ack == 'Ready':
			self.request.send('Known')
		data_type = self.request.recv(1024)
		if data_type == 'Finished': return 'Finished'
		if data_type == 'Error': 
			self.request.send('TellMeWhy')
			ack = self.request.recv(1024)
			put_message = ['PUT']
			self.logging('FAILED', *put_message)
			return 'Error'
		path = data_type[:-4]
		if data_type[-4:] == 'dirr':
			create_dir = 'mkdir' + ' ' +  path
			put_status, put_result = commands.getstatusoutput(create_dir)
			self.request.send('DIR_CREAT_SUCCEED')
			put_message = ['PUT DIR', repr(path)]
			self.logging('SUCCEED', *put_message)
		elif data_type[-4:] == 'file':
			self.request.send('Ready_Write')
			file_size = self.request.recv(1024)
			file_written = 0

			if file_size == 'EMPTY_FILE':
				get_status, get_result = commands.getstatusoutput('touch ' + path)
				self.request.send('Written_End')
			else:
				self.request.send('GET_FILE_SIZE')
				with open(path, 'wb') as f:
					while True:
						data_get = self.request.recv(1024)
						f.write(data_get)
						file_written += len(data_get)
						if file_written == int(file_size):
							self.request.send('Write_End')
							break
				put_message = ['PUT FILE', repr(path)]
				self.logging('SUCCEED', *put_message)




	def logging(self, record, *messages):
		timekick =  time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(time.time()))
		log = [timekick, self.client_address[0],]
		for msg in messages:
			log.append(msg)
		log_str = ' '.join(log)
		with open('ftp.log', 'a') as f:
			f.write(log_str + ' ' + record + '\n')
		print('%s  %s' % (log_str, record))
	 


if __name__ == '__main__':
	#HOST, PORT = 'localhost', 8888
	try:
		HOST, PORT = sys.argv[1], int(sys.argv[2])
		#Create the server, binging to localhost on port 8888
		server = SocketServer.ThreadingTCPServer((HOST, PORT), MyTCPHandler)

		# Activate the server; this will keep running until you
		# interrupt the program whit Ctrl-C
		server.serve_forever()
	except IndexError:
		print "Exec Like This: python server_ftp_python.py 127.0.0.1 8888"
	except socket.gaierror:
		print "Exec Like This: python server_ftp_python.py 127.0.0.1 8888"


