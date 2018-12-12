#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date	: 2018-11-29 19:04:30
# @Author  : Lewis Tian (chtian@hust.edu.cn)
# @Link	: https://lewistian.github.io
# @Version : Python3.7

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from mwin import Ui_MWin
from concurrent import futures
from contextlib import closing
from glob import glob
from urllib import request as urequest
from copy import deepcopy
from pprint import pprint
import json
import sys
import os
import shutil
import time
import datetime
import requests
import re
import threading
import ssl

MAX_WIDTH = 1920
MAX_HEIGHT = 1080

headers = {
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
	'Cookie': 'CURRENT_QUALITY=80; DedeUserID=227050458;'
}

class MWin(QMainWindow, Ui_MWin):
	'''嗶哩嗶哩盒子'''
	def __init__(self, parent=None):
		super(MWin, self).__init__(parent)
		self.setupUi(self)

		# 变量
		self.mFlag = False
		self.mPosition = None
		self.bgiPath = '' # 背景图片的路径
		self.key = None # 视频链接 id
		self.dlpath = 'download' # 下载目录
		self.vlists = [] # 获取的视频信息的链接
		self.plists = [] # 获取的图片信息的链接
		self.flists = [] # 收藏视频的aid
		self.fvlists = [] # 收藏视频解析信息列表

		self.vRetrieval = VideoRetrieval()
		self.vRetrieval.done.connect(self.resolveInfoDone)
		self.vRetrieval.error.connect(self.errorHappened)

		self.vDownlaod = VideoDownlaod()
		self.vDownlaod.updateProgress.connect(self.updateProgress)
		self.vDownlaod.updateSlice.connect(self.updateSlice)
		self.vDownlaod.dlpath = self.dlpath

		self.pRetrieval = PictureRetrieval()
		self.pRetrieval.done.connect(self.resolveInfoDone)
		self.pRetrieval.user.connect(self.resolveUserInfoDone)

		self.pDownlaod = PictureDownlaod()
		self.pDownlaod.dlpath = self.dlpath

		self.fRetrieval = FavoriteRetrieval()
		self.fRetrieval.done.connect(self.resolveInfoDone)

		self.fDownlaod = FavoriteDownlaod()

		self.setLogo()
		self.setBackgroundImage(self.bgiPath)
		self.connectSlots()

		if not os.path.exists(self.dlpath):
			os.mkdir(self.dlpath)

		if not os.path.exists(f'{self.dlpath}/images'):
			os.mkdir(f'{self.dlpath}/images')

		if not os.path.exists('cache'):
			os.mkdir('cache')

		if not os.path.exists('cache/avator'):
			os.mkdir('cache/avator')

		dlpath = f'下载目录: {self.dlpath}'
		self.vdlPathBtn.setText(dlpath)
		self.vdlPathBtn.setToolTip(dlpath)

		self.vtable.setColumnWidth(0, 50)
		self.vtable.setColumnWidth(1, 150)
		self.vtable.setColumnWidth(2, 50)
		self.vtable.setColumnWidth(4, 180)
		self.vtable.setColumnWidth(5, 50)

		for x in range(2, 6):
			self.ftable.setColumnWidth(x, 60)

	def resizeEvent(self, event):
		'''窗口大小改变，背景图的大小也要改变
		因为设置时已经定死了图片的尺寸'''
		self.setBackgroundImage(self.bgiPath)

	def mousePressEvent(self, event):
		x = (event.globalPos() - self.pos()).x()
		y = (event.globalPos() - self.pos()).y()
		if event.button() == Qt.LeftButton:
			self.mFlag = True
			self.mPosition = event.globalPos() - self.pos()
			event.accept()
	
	def mouseMoveEvent(self, QMouseEvent):
		if Qt.LeftButton and self.mFlag:  
			self.move(QMouseEvent.globalPos() - self.mPosition)
			QMouseEvent.accept()
			
	def mouseReleaseEvent(self, QMouseEvent):
		self.mFlag = False

	def connectSlots(self):
		'''关联所有信号槽'''
		# 文件菜单下 Action
		self.hPageAction.triggered.connect(lambda: self.changePage(0))
		self.vPageAction.triggered.connect(lambda: self.changePage(1))
		self.pPageAction.triggered.connect(lambda: self.changePage(2))
		self.fPageAction.triggered.connect(lambda: self.changePage(3))
		self.exitAction.triggered.connect(QCoreApplication.quit)
		
		# 设置菜单下 Action
		self.minSizeAction.triggered.connect(self.modifyMinSize)
		self.bgiPathAction.triggered.connect(self.modifyBGIPath)
		self.downloadPathaction.triggered.connect(self.modifyDLPath)
		self.pathAction.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(self.dlpath)))

		# 关于菜单下 Action
		self.authorAction.triggered.connect(lambda: QDesktopServices.openUrl(QUrl('https://github.com/LewisTian')))
		self.appAction.triggered.connect(lambda: QDesktopServices.openUrl(QUrl('https://github.com/LewisTian/bili-box')))

		# 按钮
		self.searchBtn.clicked.connect(self.resolveInput)
		self.vdlPathBtn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(self.dlpath)))
		self.vdownloadBtn.clicked.connect(lambda: self.download(0))
		# self.vdlAllBox.clicked.connect(self.isAllDownload)
		self.pdownloadBtn.clicked.connect(lambda: self.download(1))
		self.fdownloadBtn.clicked.connect(lambda: self.download(2))

	def changePage(self, index):
		'''修改当前页'''
		self.stackedWidget.setCurrentIndex(index)

	def setLogo(self):
		'''根据季节来更换logo(当前只有秋冬的;3)'''
		self.logo.setOpenExternalLinks(True)
		month = datetime.datetime.now().month
		link = '<a href=http://space.bilibili.com/9272615><img src={src}></a>'
		if 3 <= month <= 5:
			src = 'images/bili-spring.png'
			self.logo.setText(link.format(src=src))
			self.logo.setToolTip('嗶哩嗶哩春~')
		elif 6 <= month <= 8:
			src = 'images/bili-summer.png'
			self.logo.setText(link.format(src=src))
			self.logo.setToolTip('嗶哩嗶哩夏~')
		elif 9 <= month <= 11:
			src = 'images/bili-autumn.png'
			self.logo.setText(link.format(src=src))
			self.logo.setToolTip('嗶哩嗶哩秋~')
		else:
			src = 'images/bili-winter.png'
			self.logo.setText(link.format(src=src))
			self.logo.setToolTip('嗶哩嗶哩冬~')

	def setBackgroundImage(self, path='images/background/background.jpg'):
		'''设置主窗口的背景图片'''
		if self.bgiPath == '':
			self.bgiPath = self.readSetting(0)
			if not self.bgiPath:
				return
		elif self.bgiPath != path:
			'''如果更新背景图片则将其复制到 background 目录并删除原来的图片'''
			bgi = os.listdir('images/background')[0]
			os.remove(f'images/background/{bgi}')
			_, ext = os.path.splitext(path)
			self.bgiPath = f'images/background/background{ext}'
			shutil.copyfile(path, self.bgiPath)
			self.modifySetting(self.bgiPath, 0)

		self.setAutoFillBackground(True)
		pal = self.palette()
		pixmap = QPixmap(f'{self.bgiPath}').scaled(self.size())
		pal.setBrush(QPalette.Background, QBrush(pixmap))
		self.setPalette(pal)

	def readSetting(self, index=0):
		'''读取第index行数据'''
		try:
			with open('settting.ini') as f:
				return f.readlines()[index]
		except Exception as e:
			return None

	def modifySetting(self, newdata, index=0):
		'''修改第index行数据'''
		try:
			with open('settting.ini') as f:
				lines = f.readlines()
			lines[index] = newdata
			with open('settting.ini', 'w') as f:
				f.write(''.join(lines))
		except Exception as e:
			return None
	
	def modifyMinSize(self):
		'''修改窗口的最小尺寸（默认是(960, 540)）'''
		text, okPressed = QInputDialog.getText(self, '修改窗口尺寸', '输入尺寸:', QLineEdit.Normal, "输入两个数字 以空格分割")
		if okPressed and text != '':
			raw = text.split(' ')
			try:
				x, y = int(raw[0]), int(raw[1])
			except:
				return

			self.setMinimumSize(x, y)
			self.resize(x, y)
			
			try:
				with open(f'/mwin.py', encoding='utf-8') as f:
					lines = f.readlines()
			except Exception as e:
				return
			template1 = f'		MWin.setMinimumSize(QtCore.QSize({x}, {y}))\n'
			template2 = f'		MWin.resize({x}, {y})\n'
			for i, x in enumerate(lines):
				if x.find('resize') > 0:
					lines[i] = template2
				if x.find('setMinimumSize') > 0:
					lines[i] = template1
					break
			with open('mwin.py', 'w', encoding='utf-8') as f:
				f.write(''.join(lines))

	def modifyBGIPath(self):
		'''修改背景图片(最好比例为16x9)'''
		filename, ext = QFileDialog.getOpenFileName(self, '选择背景图片', 
			QStandardPaths.standardLocations(QStandardPaths.PicturesLocation)[0], 
			'Images (*.png *.jpg)')
		if filename != '':
			self.setBackgroundImage(filename)

	def modifyDLPath(self):
		dlpath = QFileDialog.getExistingDirectory(self, '选择下载路径', ".")
		if not dlpath: return
		self.dlpath = dlpath
		dlpath = f'下载目录:{self.dlpath}'
		self.vdlPathBtn.setText(dlpath)
		self.vdlPathBtn.setToolTip(dlpath)

	def resolveInput(self):
		index = self.comboBoxHome.currentIndex()
		text = self.lineEditHome.text()
		if text.strip(' ') == '':
			return
		if index == 0:
			try:
				key = re.findall(r'av(\d+)', text)[0]
			except Exception as e:
				return
			if not key: return
			if self.key and self.key == key:
				'''避免重复请求'''
				return
			self.key = key
			# self.request()
			self.vRetrieval.key = self.key
			self.vRetrieval.start()
		elif index == 1:
			try:
				self.mid = re.findall(r'com/(\d+)', text)[0]
			except Exception as e:
				return
			# self.request(index)
			self.pRetrieval.mid = self.mid
			self.pRetrieval.start()
		elif index == 2:
			try:
				keys = re.findall(r'com/(\d+)/favlist\?fid=(\d+)', text)[0]
				self.mid, self.fid = keys
			except Exception as e:
				self.errorHappened('输入错误！链接应该如下所示:\nhttp://space.bilibili.com/9272615/favlist?fid=10086 ')
				return
			if not os.path.exists('Cookie.txt'):
				self.errorHappened('要获取收藏信息，请先保存cookie到当前程序目录下的Cookie.txt')
				return
			self.fRetrieval.mid = self.mid
			self.fRetrieval.fid = self.fid
			self.fRetrieval.start()
			# self.request(index)
		else:
			pass

	def request(self, btype=0):
		'''根据请求类型构造请求'''
		if btype == 0:
			url = f'https://www.bilibili.com/video/av{self.key}'
			r = requests.get(url, headers=headers).text
			title = re.findall(r'<h1 title="(.*?)">', r)[0].replace(' ','-')
			cover = re.findall(r'<meta.*?itemprop="image" content="(.*?)"/><meta', r)
			print(title, cover)
		elif btype == 1:
			page = 0
			next_offset = 0
			has_more = 1
			while has_more:
				url = f'http://api.vc.bilibili.com/link_draw/v1/doc/ones?poster_uid={self.mid}&page_size=20&next_offset={next_offset}'
				# url = f'http://api.vc.bilibili.com/link_draw/v1/doc/doc_list?uid={self.mid}&page_num={page}&page_size=30&biz=all'
				print(url)
				try:
					r = requests.get(url, headers=headers).json()
				except Exception as e:
					print(e)
					return
				data = r['data']
				has_more = data['has_more']
				next_offset = data['next_offset']
				items = data['items']
				for x in items:
					description = x['description']
					upload_time = x['upload_time']
					view_count = x['view_count']
					collect_count = x['collect_count']
					like_count = x['like_count']
					pictures = x['pictures']
					print(description, upload_time, view_count, collect_count, like_count)
					for i in pictures:
						print(i['img_src'])
		elif btype == 2:
			fheaders = deepcopy(headers)
			try:
				with open('Cookie.txt') as f:
					fheaders['Cookie'] = f.read()
			except Exception as e:
				return
			total = 30
			count = 0
			p = 1
			while count < total:
				url = f'http://api.bilibili.com/x/space/fav/arc?vmid={self.mid}&ps=30&fid={self.fid}&tid=0&keyword=&pn={p}&order=fav_time&jsonp=jsonp'
				try:
					r = requests.get(url, headers=fheaders).json()
				except Exception as e:
					print(e)
					return
				data = r['data']
				total = data['total']
				count += 30
				p += 1
				pprint(data)
		else:
			pass
	
	def resolveInfoDone(self, btype, info):
		'''解析线程完成返回相关信息
		btype 类型 1 => 视频 2=> 图片
		1: info：序号 分p标题 标题 时长 大小 链接
		2: info 列表：[description, upload_time, view_count, collect_count, like_count, pics]
		3: info 列表：[aid,up,title,view,like,favorite,coin,tname,description]
		'''
		self.stackedWidget.setCurrentIndex(btype)
		if btype == 1:
			row = self.vtable.rowCount()
			self.vtable.insertRow(row)
			self.vtable.setItem(row, 0, QTableWidgetItem(str(row+1)))
			self.vtable.setItem(row, 1, QTableWidgetItem(info[1]))
			self.vtable.setItem(row, 2, QTableWidgetItem(info[3]))
			self.vtable.setItem(row, 3, QTableWidgetItem(f'{info[4]}M'))
			qpb = QProgressBar()
			qpb.setValue(0)
			self.vtable.setCellWidget(row, 4, qpb)
			self.vtable.setItem(row, 5, QTableWidgetItem(f'0/{len(info[-1])}'))
			self.vtable.setItem(row, 6, QTableWidgetItem(info[2]))
			for x in range(7):
				try:
					self.vtable.item(row, x).setTextAlignment(Qt.AlignCenter)
				except Exception as e:
					pass # 显示进度条的列会报错
			self.vlists.append(info[-1])
			
		elif btype == 2:
			for i in info:
				row = self.ptable.rowCount()
				self.ptable.insertRow(row)
				for x in range(5):
					self.ptable.setItem(row, x, QTableWidgetItem(i[x]))
					self.ptable.item(row, x).setTextAlignment(Qt.AlignCenter)
				self.ptable.setItem(row, 5, QTableWidgetItem(str(len(i[5]))))
				self.ptable.item(row, x).setTextAlignment(Qt.AlignCenter)
				self.ptable.setItem(row, 6, QTableWidgetItem(';'.join(i[5])))
				self.plists.append(i[5])
		elif btype == 3:
			for i in info:
				row = self.ftable.rowCount()
				self.ftable.insertRow(row)
				for x in range(len(i)-1):
					self.ftable.setItem(row, x, QTableWidgetItem(i[x+1]))
					self.ftable.item(row, x).setTextAlignment(Qt.AlignCenter)
				self.flists.append(i[0])
		else:
			pass

	def resolveUserInfoDone(self, info):
		pix = QPixmap(info[1])
		self.pavator.setPixmap(pix)
		self.pavator.setScaledContents(True)
		self.pavator.setToolTip(info[0])
		self.pname.setText(info[0])
		self.pname.setToolTip(info[0])

	def errorHappened(self, msg='发生了一个错误，请重试...'):
		QMessageBox.warning(self, '嗶哩嗶哩盒子©Lewis Tian', msg, QMessageBox.Ok)

	def isAllDownload(self):
		'''是否下载全部视频'''
		if self.vdlAllBox.isChecked():
			self.vtable.setRangeSelected(
					QTableWidgetSelectionRange(0, 0, 
						self.vtable.rowCount()-1, self.vtable.columnCount()-1), 
					True)

	def download(self, dtype):
		'''分发下载链接
		dtype 0: 视频
			  1: 图片 
			  2: 收藏'''
		if dtype == 0:
			if self.vdlAllBox.isChecked():
				rows = [x for x in range(self.vtable.rowCount())]
			else:
				rows = [x for x in range(self.vtable.rowCount()) if self.vtable.item(x, 0).isSelected()]
			if not rows: return
			for x in rows[::-1]:
				val = self.vtable.cellWidget(x, 4).value()
				if val == 100: rows.remove(x)
			self.vDownlaod.num = rows
			self.vDownlaod.urls = [self.vlists[x] for x in rows]
			self.vDownlaod.start()
		elif dtype == 1:
			if self.pdlAllBox.isChecked():
				rows = [x for x in range(self.ptable.rowCount())]
			else:
				rows = [x for x in range(self.ptable.rowCount()) if self.ptable.item(x, 0).isSelected()]
			if not rows: return
			self.pDownlaod.num = rows
			self.pDownlaod.urls = [self.plists[x] for x in rows]
			self.pDownlaod.start()
		elif dtype == 2:
			rows = [x for x in range(self.ftable.rowCount()) if self.ftable.item(x, 0).isSelected()]
			if not rows: return
			# self.fDownlaod.num = rows
			# self.fDownlaod.aids = [self.flists[x] for x in rows]
			# self.fDownlaod.start()
			aids = [self.flists[x] for x in rows]
			threads = []
			for i, j in enumerate(aids):
				t = VideoRetrieval()
				t.done.connect(self.resolveInfoDone)
				t.error.connect(self.errorHappened)
				t.key = j
				threads.append(t)
			self.fvlists.append(threads)
			for t in self.fvlists[-1]:
				t.start()
		else:
			pass

	def updateProgress(self, row, percent):
		'''更新进度条'''
		self.vtable.cellWidget(row, 4).setValue(percent)

	def updateSlice(self, row, p):
		slices = self.vtable.item(row, 5).text().split('/')[1]
		self.vtable.setItem(row, 5, QTableWidgetItem(f'{p}/{slices}'))
		self.vtable.item(row, 5).setTextAlignment(Qt.AlignCenter)

class VideoRetrieval(QThread):
	'''获取视频下载链接'''
	done = pyqtSignal(int, list)
	error = pyqtSignal()
	def __init__(self):
		super(VideoRetrieval, self).__init__()

	def run(self):		
		url = f'https://www.bilibili.com/video/av{self.key}'
		r = requests.get(url, headers = headers).text
		try:
			title = re.findall(r'<h1 title="(.*?)">', r)[0].replace(' ','-')
		except Exception as e:
			'''视频不见了'''
			self.error.emit()
			return
		self.title = title
		# cover = re.findall(r'<meta.*?itemprop="image" content="(.*?)"/><meta', r)
		# self.cover = cover
		pages = re.findall(r'page":(.*?),"from":"vupload","part":"(.*?)","duration":', r) 
		if not pages:
			'''可能是番剧、电影啥的无法解析出来'''
			self.error.emit()
			return
		with futures.ThreadPoolExecutor(32) as executor:
			executor.map(self.resolve, pages)

	def resolve(self, page):
		'''获取每个分p的视频链接
		page: (index, page title)
		'''
		url = f'https://www.bilibili.com/video/av{self.key}?p={page[0]}'
		r = requests.get(url, headers = headers).text
		regex = '"order":(.*?),"length":(.*?),"size":(.*?),.*?"url":"(.*?)"'
		result = re.findall(regex, r) # 序号 时长 大小 链接
		time = str(sum([int(i[1]) for i in result])//60000) +":"+str(int((sum([int(i[1]) for i in result])%60000)//1000))
		size = round(sum([int(i[2]) for i in result])/1024/1024, 1)
		url = [i[3] for i in result]
		ret = list(page) + [self.title, time, size, url] # [类型] 序号 分p标题 标题 时长 大小 链接
		threading.Thread(target=self.dumpInfo, args=(self.key, ret)).start()
		self.done.emit(1, ret)

	def dumpInfo(self, aid, info):
		if os.path.exists(f'cache/av{aid}.json'): return
		r = {}
		r['aid'] = aid
		r['ptitle'] = info[1]
		r['title'] = info[2]
		r['duration'] = info[3]
		r['size'] = info[4]
		r['urls'] = info[5]
		with open(f'cache/av{aid}.json', 'w', encoding = 'utf-8') as f:
			json.dump(r, f, ensure_ascii=False, indent=4)

class VideoDownlaod(QThread):
	'''使用多线程下载视频'''
	updateProgress = pyqtSignal(int, int) # row percent
	updateSlice = pyqtSignal(int, str) # row, current slice
	def __init__(self):
		super(VideoDownlaod, self).__init__()

	def run(self):
		'''self.urls是个二维数组：多个视频，多个分p'''
		self.percent = 0
		threads = []
		for i, j in enumerate(self.num):
			t = threading.Thread(target=self.download, args=(self.urls[i], ), name=str(j))
			threads.append(t)
		
		self.threadLock = threading.Lock()
		for j in threads:
			j.start()

	def download(self, url):
		ssl._create_default_https_context = ssl._create_unverified_context
		opener = urequest.build_opener()
		opener.addheaders = [
				('Host', 'tx.acgvideo.com'),
				('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',),
				('Accept', '*/*'),
				('Accept-Language', 'en-US,en;q=0.5'),
				('Accept-Encoding', 'gzip, deflate, br'),
				('Range', 'bytes=0-'),  # Range 的值要为 bytes=0- 才能下载完整视频
				('Referer', 'https://www.bilibili.com/video/av14543079/'),
				('Origin', 'https://www.bilibili.com'),
				('Connection', 'keep-alive'),
			]
		urequest.install_opener(opener)

		folder = self.dlpath + '/' + url[0].split('?')[0].split('/')[-1].split('-')[0]
		for i, j in enumerate(url):
			filename = j.split('?')[0].split('/')[-1]
			print(f'path: {folder}/{filename}\n')
			if not os.path.exists(folder):
				os.mkdir(folder)
			if os.path.exists(f'{folder}/{filename}'):
				self.updateProgress.emit(int(threading.current_thread().name), 100)
				continue
			urequest.urlretrieve(j, filename=f'{folder}/{filename}', reporthook=self.report)
			self.updateSlice.emit(int(threading.current_thread().name), str(i+1))
		if len(url) > 1:
			self.merge(folder)
		else:
			self.change2mp4(folder)
		
	def report(self, count, blockSize, totalSize):
		downloadedSize = count * blockSize
		percent = int(downloadedSize * 100 / totalSize)
		if not self.percent == percent:
			self.percent = percent
			self.updateProgress.emit(int(threading.current_thread().name), percent)

	def merge(self, folder):
		'''若是分片>1则会合并视频'''
		files = glob(folder+'/*.flv')
		outlists = []
		for i, x in enumerate(files):
			outfile = f'{folder}/{i}.ts'
			outlists.append(outfile)
			print(x, outfile)
			s = f'ffmpeg.exe -i {x} -vcodec copy -acodec copy -vbsf h264_mp4toannexb {outfile}'
			os.popen(s)
		s = f'''ffmpeg.exe -y -i "concat:{'|'.join(outlists)}" -acodec copy -vcodec copy -absf aac_adtstoasc {folder}/{folder.split('/')[-1]}.mp4'''
		os.popen(s)
		for x in outlists:
			os.remove(x)

	def change2mp4(self, folder):
		files = glob(folder+'/*.flv')
		for i, x in enumerate(files):
			out = folder.split('/')[-1]
			s = f'''ffmpeg -y -i {x} -c copy {folder}/{out}.mp4'''
			os.popen(s)

class PictureRetrieval(QThread):
	'''获取图片信息'''
	done = pyqtSignal(int, list)
	user = pyqtSignal(list)
	error = pyqtSignal()
	def __init__(self):
		super(PictureRetrieval, self).__init__()

	def run(self):
		page = 0
		next_offset = 0
		has_more = 1
		set_user = False
		while has_more:
			plist = []
			url = f'http://api.vc.bilibili.com/link_draw/v1/doc/ones?poster_uid={self.mid}&page_size=20&next_offset={next_offset}'
			# url = f'http://api.vc.bilibili.com/link_draw/v1/doc/doc_list?uid={self.mid}&page_num={page}&page_size=30&biz=all'
			try:
				r = requests.get(url, headers=headers).json()
			except Exception as e:
				print(e)
				return
			data = r['data']
			has_more = data['has_more']
			next_offset = data['next_offset']
			items = data['items']
			if not set_user:
				self.getUserAvator(data['user'])
				set_user = True
			for x in items:
				p = []
				description = x['description']
				upload_time = x['upload_time']
				view_count = x['view_count']
				collect_count = x['collect_count']
				like_count = x['like_count']
				pictures = x['pictures']
				pics = [i['img_src'] for i in pictures]
				# print(description, upload_time, view_count, collect_count, like_count)
				p = [description, upload_time, str(view_count), str(collect_count), str(like_count), pics]
				plist.append(p)
			self.done.emit(2, plist)
		print('over')

	def getUserAvator(self, info):
		name = info['head_url'].split('/')[-1]
		path = f'cache/avator/{name}'
		if not os.path.exists(path):
			r = requests.get(info['head_url'], headers = headers)
			with open(path, 'wb') as f:
				f.write(r.content)
		self.user.emit([info['name'], path])

class PictureDownlaod(QThread):
	'''使用多线程下载图片'''
	def __init__(self):
		super(PictureDownlaod, self).__init__()

	def run(self):
		threads = []
		for i, j in enumerate(self.num):
			t = threading.Thread(target=self.download, args=(self.urls[i], ), name=str(j))
			threads.append(t)

		for j in threads:
			j.start()

	def download(self, url):
		for x in url:
			name = x.split('/')[-1]
			path = f'{self.dlpath}/images/{name}'
			if not os.path.exists(path):
				urequest.urlretrieve(x, filename = path)

class FavoriteRetrieval(QThread):
	'''获取收藏信息'''
	done = pyqtSignal(int, list)
	error = pyqtSignal()
	def __init__(self):
		super(FavoriteRetrieval, self).__init__()

	def run(self):
		total = 30
		count = 0
		page = 1
		fheaders = deepcopy(headers)
		try:
			with open('Cookie.txt') as f:
				fheaders['Cookie'] = f.read()
		except Exception as e:
			print('要获取收藏信息，请先保存cookie到当前程序目录下的Cookie.txt')
			return
		while count < total:
			flist = []
			url = f'http://api.bilibili.com/x/space/fav/arc?vmid={self.mid}&ps=30&fid={self.fid}&tid=0&keyword=&pn={page}&order=fav_time&jsonp=jsonp'
			print(url)
			try:
				r = requests.get(url, headers=fheaders).json()
			except Exception as e:
				self.error.emit()
				return
			try:
				data = r['data']
			except Exception as e:
				print(e)
				return
			total = data['total']
			count += 30
			page += 1
			for x in data['archives']:
				p = []
				aid = x['aid']
				up = x['owner']['name']
				title = x['title']
				view = x['stat']['view']
				like = x['stat']['like']
				favorite = x['stat']['favorite']
				coin = x['stat']['coin']
				tname = x['tname']
				description = x['desc'].replace('\n', ' ')
				p = [aid,up,title,str(view),str(like),str(favorite),str(coin),tname,description]
				flist.append(p)
			threading.Thread(target=self.dumpInfos, args=(flist,)).start()
			self.done.emit(3, flist)
		print('over')

	def dumpInfos(self, info):
		header = ['aid','up','title','view','like','favorite','coin','tname','description']
		for x in info:
			if os.path.exists(f'cache/fav{x[0]}.json'): continue
			r = {}
			for i, j in enumerate(header):
				r[j] = x[i]
			with open(f'cache/fav{x[0]}.json', 'w', encoding = 'utf-8') as f:
				json.dump(r, f, ensure_ascii=False, indent=4)

class FavoriteDownlaod(QThread):
	"""docstring for FavoriteDownlaod"""
	def __init__(self):
		super(FavoriteDownlaod, self).__init__()
	
	def run(self):
		threads = []
		for i, j in enumerate(self.num):
			t = threading.Thread(target=self.download, args=(self.aids[i], ), name=str(j))
			threads.append(t)

		for j in threads:
			j.start()

	def download(self, aid):
		print(aid)

def mainSplash():
	'''启动画面'''
	app = QApplication(sys.argv)
	pixmap = QPixmap('images/background.jpg').scaled(720, 405)
	splash = QSplashScreen(pixmap)
	splash.showMessage('正在加载资源中...', Qt.AlignLeft | Qt.AlignBottom, Qt.white)
	splash.show()
	app.processEvents()
	time.sleep(2)
	w = MWin()
	w.show()
	splash.finish(w)
	del splash
	app.exec()

def main():
	app = QApplication(sys.argv)
	w = MWin()
	w.show()
	sys.exit(app.exec_())

if __name__ == '__main__':
	main()