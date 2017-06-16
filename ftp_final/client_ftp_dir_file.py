#! /usr/bin/env python
# -*- coding: utf8 -*-
# filename: client_ftp.py

import socket
import time
import commands
import os

HOST = raw_input('Input the ftp ip:').strip()

PORT = int(raw_input("Input the ftp port:").strip())

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

def get():
	#print "Waitting file's type!\n"
	ack = s.recv(1024)
	#print('ACK IS %s' % ack)
	if ack == 'Finished':
		return 'Finished'
	if ack == 'EMPTY_DIR':
		return 'EMPTY_DIR'
	if ack == 'Ready':
		s.send('Known')
	data_type = s.recv(1024)
	if data_type == 'Finished': return 'Finished'
	if data_type == 'Error': 
		s.send('TellMeWhy')
		print s.recv(1024)
		return 'Error'
	path = data_type[:-4]
	if data_type[-4:] == 'dirr':
		create_dir = 'mkdir' + ' ' +  path
		get_status, get_result = commands.getstatusoutput(create_dir)
		s.send('DIR_CREAT_SUCCEED')
		if get_status == 0:
			pass
			#print 'GET DIR %s SUCCEED!\n' % path
	elif data_type[-4:] == 'file':
		s.send('Ready_Write')
		file_size = s.recv(1024)
		file_written = 0
		
		if file_size == 'EMPTY_FILE':
			get_status, get_result = commands.getstatusoutput('touch ' + path)
			s.send('Written_End')
		else:
			s.send('GET_FILE_SIZE')
			with open(path, 'wb') as f:
				while True:
					data_get = s.recv(1024)
					f.write(data_get)
					file_written += len(data_get)
					if file_written == int(file_size):
						s.send('Write_End')
						break
			#print 'GET FILE %s SUCCEED!' % path

def put(*obj_list):
	file_and_dir_list = []
	file_list = []
	dir_list = []
	
	
	for obj in obj_list:
		status, result = commands.getstatusoutput('ls ' + obj + ' -d')		
		if status != 0:
			s.send('Ready')
			ack = s.recv(1024)
			if ack == 'Known':
				s.send('Error')
			ack = s.recv(1024)
			if ack == 'TellMeWhy':
				s.send("No Such File %s" % repr(obj))
				print("No Such File %s" % repr(obj))
				return 'Error'
			continue

		if os.path.isdir(obj):
			s.send('Ready')
			ack = s.recv(1024)
			if ack == 'Known':
				s.send(obj + 'dirr')
			ack = s.recv(1024)
			if ack == 'DIR_CREAT_SUCCEED':
				pass
			file_and_dir_list = os.listdir(obj)
			if len(file_and_dir_list) == 0:
				s.send('EMPTY_DIR')
				continue
			else:
				for file_obj in file_and_dir_list:
					obj_path = obj + '/' + file_obj
					if os.path.isdir(obj_path):
						dir_list.append(obj_path)
					else:	
						file_list.append(obj_path)
						s.send('Ready')
						ack = s.recv(1024)
						if ack == 'Known':
							s.send(obj_path + 'file')
						ack = s.recv(1024)
						if ack == 'Ready_Write':
							file_size = os.path.getsize(obj_path)
							if file_size == 0:
								s.send('EMPTY_FILE')
							else:
								s.send(str(file_size))
								ack = s.recv(1024)
								if ack == 'GET_FILE_SIZE':
									with open(obj_path, 'rb') as f:
										while True:
											data_read = f.read(1024)
											if len(data_read) == 0: break
											s.sendall(data_read)
						ack = s.recv(1024)
						if ack == 'Write_End':
							pass
							#print("PUT FILE %s SUCCEED!" % obj_path)
		else:
			s.send('Ready')
			ack = s.recv(1024)
			if ack == 'Known':
				s.send(obj + 'file')
			ack = s.recv(1024)
			if ack == 'Ready_Write':
				file_size = os.path.getsize(obj)
				if file_size == 0:
					s.send('EMPTY_FILE')
				else:
					s.send(str(file_size))
					ack = s.recv(1024)
					if ack == 'GET_FILE_SIZE':
						with open(obj, 'rb') as f:
							while True:
								data_read = f.read(1024)
								if len(data_read) == 0: break
								s.sendall(data_read)
			ack = s.recv(1024)
			if ack == 'Write_End':
				pass
				#print("PUT FILE %s SUCCEED!" % obj)
		if len(dir_list) != 0:
			put(*dir_list)
	return 'Finished'		


while 1:
	cmd = raw_input('ftp>>>').strip()
	if len(cmd) == 0: continue
	action = cmd.split()
	if action[0] == 'exit':
		print 'bye'
		s.sendall(cmd)
		break
	s.sendall(cmd)
	if action[0] == 'get':
		while True:
			status = get() 
			if status == 'Finished':
				print "GET SUCCEED"
				break
			elif status == 'Error':break
			elif status == 'EMPTY_DIR':continue
	elif action[0] == 'put':
		try:
			put_list = action[1:]
			status = put(*put_list)
			time.sleep(0.002)
			s.send('Finished')
			if status == 'Finished':
				print('PUT SUCCEED!')
			elif status == 'Error':
				pass
		except Exception:
			print 'Error Hanppened'
	else:
		print s.recv(1024)
s.close




