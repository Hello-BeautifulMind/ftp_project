# Ftp_project
学习socket，实现简单多用户在线的FTP程序
***
## 内容
* [环境介绍](#环境介绍)
* [安装使用](#安装使用)
* [示例](#示例)

### 环境介绍
-----------
* OS and Python:

  - Windows 10
  - Python 3.5.1
  
### 安装使用
-----------
1. 先运行ftp_server_v1.py然后再运行ftp_client_v1.py
2. 在代码所在的上一层目录创建ftp_download文件夹，作为用户登录的根目录
3. 在ftp_download文件夹下创建可登录用户文件夹以及存放待用户下载文件的文件夹<br>
   最终目录结构类似这样：
   * ftp_download
   	 - 文件夹1
	 - 文件夹2
	 - users
	   - sam.txt -- 用户sam的个人信息（格式为：“用户名   密码(MD5处理过的)   .,文件夹1,文件夹2”）
	   - tom.txt -- 用户tom的个人信息
4. 用户登录后输入的命令格式：“命令  参数1 参数2”，如<br>
   下载文件命令：get  example.avi<br>
   切换目录：cd ../movie<br>
   查看当前目录文件：dir
   
### 示例
-----------
1. 下载文件<br>
命令：get example.avi<br> 
[客户端下载](/images/client.png)<br>
[服务端信息](/images/server.png)


