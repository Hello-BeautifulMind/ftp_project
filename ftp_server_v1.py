'''
创建一个TcpServer
1）创建一个请求处理类[RequestHandle class]，并且这个类要继承
	BaseRequestHandler,并且重写父类的handle（）方法处理请求用
2）实例化TCPServer，并且传递(server_ip, port) 和你上面创建的请求处理类给这个TCPServer
3）调用
4）关闭
'''
import socketserver, os, hashlib, re, subprocess

class MyTCPServer(socketserver.BaseRequestHandler):
	'''
	handle:
	1）死循环，提示相关信息.
	2）验证客户账户和密码
	3）拆分指令，获取指令和文件名，判断文件是否存在，做相应处理
	4）发送文件大小
	5）获取文件续传点（调用续传方法）
	6）修改文件指针，发送数据
	'''
	def handle(self):
		while True:
			# 验证用户名和密码
			print("等待输入身份认证...")
			user = self.request.recv(1024)					# 接收登录账号
			self.request.send(b"username recv.")			# 防止粘包，因为客户端同时发送账号和密码时可能在第一次就被接收完
			pwd = self.request.recv(1024)					# 接收密码

			pass_stat = self.authentication(user.decode(), pwd.decode())
			
			if not pass_stat:								# 认证失败
				self.request.send(b"Failed")				# 发送认证结果
				continue
			self.request.send(b"Success")					# 发送认证结果

			while True:
				print("等待客户端指令...")
				order = self.request.recv(1024).decode().strip()	# 字符类型
				order_list = order.split()							# 将命令和参数转成列表形式
				handle_res = self.handle_order(order_list)				# 返回命令处理结果
				if handle_res == "exit":
					print("客户端已经断开")	# 只是该连接对象断开，但是服务器还是运行着的
					return 0

				elif handle_res == "Invalid_order":		# 不在列表的命令
					print("%s 命令无效" % order_list[0])
					continue

				elif handle_res == "download_file":		# 下载文件
					filename = order_list[1]			# 下载的文件名
					self.download_file(filename)		# 调用下载文件的方法

				elif handle_res == "change_dir":		# 切换目录
					directory = os.path.join(self.cur_dir, order_list[1])# 目录路径
					self.change_dir(directory)			# 调用改变路径的方法

				elif handle_res == "other_order":
					self.other_order(order)
				

	# 处理指令
	def handle_order(self, order_list):
		if not order_list:							# 如果没有指令，说明客户端已经断开
			return "exit"							# 客户端已经断开返回exit

		cmd = order_list[0]
		if cmd not in self.order_list:				# 命令没在列表中，返回
			return "Invalid_order"

		parameters_length = len(order_list) - 1		# 参数个数

		if cmd == "get" and parameters_length == 1:	# get 命令且参数只有一个(文件名)则下载文件
			return "download_file"
		if cmd == "cd" and parameters_length == 1:	# cd 命令且参数只有一个切换目录
			return "change_dir"
		
		return "other_order"
				

	# 用户认证
	def authentication(self, user, pwd):
		print("登录账号：", user)
		print("登录密码：", pwd)

		if not os.path.isfile("../ftp_download/users/" + user + ".txt"):		# 如果用户文件不存在，返回False
			return False

		with open("../ftp_download/users/" + user + ".txt") as userfile:		# 打开用户文件
			user_info = userfile.read().split()								# 分割用户各个字段
			login_name = user_info[0]										# 用户登录账号
			login_pwd = user_info[1]											# 用户登录密码（MD5）
			#access_authority = [] if len(user_info) < 2 else user_info[2]	# 用户访问权限

			print("用户信息：")
			for u in user_info:		# 打印用户信息
				print(u)

			if user == login_name and pwd == login_pwd:
				self.user_info = user_info					# 存储用户信息
				self.root_dir = "../ftp_download/"			# 存储用户根目录
				self.cur_dir = "../ftp_download/"			# 存储用户当前目录
				self.order_list = ["get", "cd", "dir", "ipconfig"]		# 可执行的命令
				print("Authentication success")
				return True

			print("Authentication failed")
			return False

	# 获取用户信息

	# 文件下载
	def download_file(self, filename):
		if not os.path.isfile(self.cur_dir + filename):	# 下载的文件不存在
			print("'%s' file does not exits" % filename)
			self.request.send(("%s does not exits" % filename).encode())
			return False

		# 发送文件大小
		file_size = os.stat(self.cur_dir + filename).st_size
		self.request.send(str(file_size).encode())

		# 断点续传 获取客户端文件已完成情况，然后修改文件指针或者计算已发的不再发
		# 如何修改文件指针
		client_file_size = int(self.request.recv(1024).decode())
		print("客户端文件%s 已下载了%d 字节" % (filename, client_file_size))

		# 防止粘包, 接收客户状态, 暂时不需要，因为不同数据间没有连续的多个send了
		# client_stat = self.request.recv(1024)
		# print(client_stat.decode())

		# 发送数据, 设置已发送多少了, >= 0
		has_send_size = client_file_size		# # 已经发送文件大小
		#send_data_size = client_file_size		# 已经发送文件大小
		remain_size = file_size - has_send_size	# 剩下文件大小
		if remain_size <= 0:					# 文件发送完了
			print("%s has download complete" % filename)
			return False

		m = hashlib.md5()						# hash对象，生成文件校验码
		with open(self.cur_dir + filename, "rb") as file:
			# 修改文件指针
			file.seek(has_send_size)
			while remain_size > 0:
				send_data = file.read(1024)		# 从续传点每次读取1024个字节
				self.request.send(send_data)	# 一次发送1024个字节
				m.update(send_data)				# 更新hash码
				has_send_size += len(send_data)	# 计算已经发送文件大小
				remain_size -= len(send_data)	# 计算还剩多少		

			self.request.send(m.hexdigest().encode())	# 发送md5处理的hash值

			print("发送 %s 数据大小：%d, md5值: %s" % (filename, has_send_size, m.hexdigest()))

	# 更改用户路径
	def change_dir(self, directory):
		abs_dir = os.path.abspath(directory).replace("\\", "/")	# 绝对路径
		if not os.path.isdir(directory):						# 目录不存在
			print("'%s' directory does not exits" % abs_dir)
			self.request.send(("directory does not exits").encode())
			return False

		username = self.user_info[0]			# 获取当前用户
		access_authority = [] if len(self.user_info) < 3 else self.user_info[2]
		print("%s 用户能访问的目录：%s" % (username, access_authority))
		print("准备切换到 %s目录：", abs_dir)	# 打印将要切换到的目录
		print("可访问权限列表:")				# 打印客户能访问的目录
		for access_dir in access_authority.split(","):
			access_dir = os.path.abspath(self.root_dir + access_dir).replace("\\", "/")
			print(access_dir)
		access = False 							# 检查用户是否有访问权限
		for index, access_dir in enumerate(access_authority.split(",")):
			access_dir = os.path.abspath(self.root_dir + access_dir).replace("\\", "/")
			
			if index == 0:						# 如果访问的是根目录，允许
				if access_dir == abs_dir:		# 
					access = True
					break
			else:								# 并不是根目录，是否在根目录里
				if not re.search(access_dir, abs_dir) is None: 
					access = True
					break

		if access:
			print("允许访问")
			root_abs = os.path.abspath(self.root_dir).replace("\\", "/")
			self.cur_dir = self.root_dir + abs_dir[len(root_abs)+1:]
			print("切换后的当前目录,", self.cur_dir)
			self.request.send(self.cur_dir[3:].encode())		# 发送的是相对路径
		else:
			print("不允许访问")
			self.request.send(b"No access permissions")			# 不允许访问
		


	# 执行其他命令
	def other_order(self, order):
		print("将要执行 %s 命令" % order)
		
		p = subprocess.Popen(order, shell=True, stdout=subprocess.PIPE, cwd=self.cur_dir)
		order_res = p.communicate()[0]					# 获取命令执行结果，返回值是个元组
		data_length = len(order_res)					# 内容长度
		if data_length == 0:							# 执行结果为空
			msg = "The result is empty"					# 错误消息
			self.request.send(str(len(msg)).encode())	# 发送错误消息长度
			print(self.request.recv(1024).decode())		# 防止粘包
			self.request.send(msg.encode())				# 发送错误消息
			return None

		self.request.send(str(data_length).encode())	# 发送内容长度
		print(self.request.recv(1024).decode())			# 防止粘包
		print("数据长度：", data_length)				
		#
		#order_res.seek(0)								# 文件指针指向头部, 无效
		i = 0
		while True:										# 不断发送执行结果，直到没有内容
			data = order_res[i:i+1024]					# 每次尝试读取1024个字节
			if not data: break

			self.request.send(data)						# 发送读取的字节
			i += len(data)
		print("发送成功，发送的数据长度：", data_length)

if __name__ == "__main__":
	SERVER_IP, PORT = "localhost", 8888
	server = socketserver.ThreadingTCPServer((SERVER_IP, PORT), MyTCPServer)

	server.serve_forever()
	server.close()