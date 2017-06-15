import socket, os, hashlib, time

class MyTCPClient(object):
	'''
	客户端
	'''
	def __init__(self):			# 创建套接字对象，与服务端通信
		self.client = socket.socket()
	def connect(self, SERVER_IP, PORT):			# 连接服务器
		self.client.connect((SERVER_IP, PORT))
	

	def handle(self):			# 连接后处理请求的入口
		while True:
			auth = self.login_auth()			# 通过登录方法进行登录认证，返回认证结果
			if not auth:			# 如果认证不通过，继续进行登录认证
				continue
			
			while True:
				order = input(self.position)			# 输入命令和参数：格式"命令 参数1 参数2"
				order_list = order.strip().split()			# 拆分命令和参数
				handle_res = self.handle_order(order_list)			# 处理命令以调用不同方法
				if handle_res is None:
					print("Order and Parameter not null")
					continue			# 没有输入任何内容返回重新输入
				
				elif handle_res == "Invalid_order":
					print("Invalid order")
					continue

				elif handle_res == "download_file":			# 下载文件
					filename = order_list[1]			# 下载的文件名称
					self.download_file(filename)			# 传入文件名调用下载方法

				elif handle_res == "change_dir":			# 切换目录
					directory = order_list[1]			# 目录路径
					self.change_dir(directory)			# 传入目录路径调用改变路径方法
				
				elif handle_res == "other_order":			# 其他命令，其实是服务端用subprocess的Popen来调用系统命令
					self.other_order()



	# 处理命令和发送命令
	def handle_order(self, order_list):
		if not order_list: 
			return None
		cmd = order_list[0]
		if cmd not in self.order_list:
			return "Invalid_order"

		parameters_length = len(order_list) - 1

		self.client.send(" ".join(order_list).encode())			# 发送命令 和服务器对应
		if cmd == "get" and parameters_length == 1:
			return "download_file"
		if cmd == "cd" and parameters_length == 1:
			return "change_dir"

		return "other_order"



	# 登录认证
	def login_auth(self):
		"""
			1）发送账号、接收账号确认、发送密码、接收认证结果
		"""
		user = input("Username:")
		pwd = input("Password:")

		if not user.strip() or not pwd.strip():			# 用户名和密码都不能为空
			print("Username and Password not null.")
			return False

		pwd_md5 = hashlib.md5()			# 使用md5方式加密密码
		pwd_md5.update(pwd.encode())			# 更新hash值
		self.client.send(user.encode())			# 发送用户名
		self.client.recv(1024)			# 接收一条数据，防止在发送密码时粘包
		self.client.send(pwd_md5.hexdigest().encode())			# 发送md5密码
		pass_stat = self.client.recv(1024)			# 接收认证结果
		
		if pass_stat.decode() == "Failed":			# 认证失败
			print("Authentication failed")			# 打印认证结果
			return False 			# 认证失败，继续输入账号密码登录
			
		print("Authentication success")			# 认证成功
		self.position = "ftp_download >>"			# 用户初始位置
		self.order_list = ["get", "cd", "dir", "ipconfig"]			# 可执行的命令
		return True

	# 下载文件
	def download_file(self, filename):
		# filename = cmd.strip().split()[-1]			# 获取下载文件名
		
		file_stat = self.client.recv(1024)			# 接收服务器对文件的处理情况

		if file_stat.decode() == "{file_name} does not exits".format(file_name=filename):			# 文件不存在
			print("%s does not exits" % filename)			# 文件不存在
			return False

		file_size = int(file_stat.decode())			# 接收文件大小

		open_resume = True			# 是否开启续传功能，False时文件都重新下载
		file_mode = "ab"			# 文件打开方式，续传时以追加方式，否则以wb方式
		
		if not os.path.isfile(filename) or not open_resume:			# 如果文件还不曾下载过，该文件大小设置为0
			cur_file_size = 0
			file_mode = "wb"
		else:			# 否则设置当前文件大小
			cur_file_size = os.stat(filename).st_size
		self.client.send(str(cur_file_size).encode())			# 发送要下载的文件已经下载的大小
		
		if cur_file_size >= file_size:			# 文件存在并且大小大于等于服务器的文件则不再下载
			print("%s has exits and file download complete." % filename)
			return False

		# 防止粘包
		#client.send(b"ok.")

		recv_file_size = cur_file_size			# 已收文件大小
		next_progress = round(cur_file_size / file_size * 100)			# 进度条，不能设置为1，因为续传时进度条不再从头开始，否则进度条会有闪烁效果（连续progress >= next_progress）
		recv_file_md5 = hashlib.md5()			# hash对象
		
		# 接收文件
		with open(filename, file_mode) as file:			# 二进制追加模式打开文件，文件不存在则创建
			while file_size > recv_file_size:
				if file_size - recv_file_size >= 1024:
					buf = 1024
				else:
					buf = file_size - recv_file_size

				recv_data = self.client.recv(buf)			# 是bytes类型，接收
				file.write(recv_data)			# 将数据写入文件
				recv_file_size += len(recv_data)			# 计算已收到文件大小
				recv_file_md5.update(recv_data)			# 更新hash值

				
				progress = round(recv_file_size / file_size * 100, 2)			# 打印进度条
				if progress >= next_progress:
					os.system("cls")			# 在windows的清屏命令
					print("file size: %d" % file_size)			# 打印文件大小
					print("recv progress: %f%%" % (recv_file_size / file_size * 100))			# 10%
					print(("#" * int(progress) + "\t").expandtabs(108), "{}%".format(progress))
					next_progress += 1
					

				# if len(recv_data) != 1024:
				# 	print(len(recv_data))

			file_md5 = self.client.recv(1024)
			print("file md5: ", file_md5.decode())
			print("recv file md5: ", recv_file_md5.hexdigest())
			print("recv success, recv file size:%d" % recv_file_size)

	# 切换目录
	def change_dir(self, directory):
		dir_stat = self.client.recv(1024).decode()

		if dir_stat == "directory does not exits":
			print("%s directory does not exits" % directory)			# 目录不存在
			return False
		print("Will view dir is: ", dir_stat)
		self.position = dir_stat + " >>"

	def other_order(self):
		print("other_order...")
		data_list = []
		remain_length = int(self.client.recv(1024).decode())			# 数据长度
		self.client.send(b"ok")			# 防止粘包
		print("Data length: ", remain_length)
		while remain_length > 0:
			recv_data = self.client.recv(1024)			# 尝试接收1024个字节
			data_list.append(recv_data)			# 每次接收的数据放进列表里
			remain_length -= len(recv_data)			# 更新长度
		order_res = b"".join(data_list).decode("utf-8")			# 拼接字节并解码
		print(order_res)			# 打印结果

	# 关闭连接
	def close(self):						
		self.client.close()



if __name__ == "__main__":
	SERVER_IP, PORT = ("localhost", 8888)
	my_client = MyTCPClient()			# 创建客户端连接对象
	my_client.connect(SERVER_IP, PORT)			# 连接服务器
	my_client.handle()			# 处理请求