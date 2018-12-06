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
		self.vlists = [] # 获取的视频信息
		self.plists = [] # 获取的图片信息

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

		self.setLogo()
		self.setBackgroundImage(self.bgiPath)
		self.connectSlots()

		if not os.path.exists(self.dlpath):
			os.mkdir(self.dlpath)

		if not os.path.exists('cache'):
			os.mkdir('cache')

		if not os.path.exists('cache/avator'):
			os.mkdir('cache/avator')

		dlpath = f'下载目录: {self.dlpath}'
		self.dlPathBtn.setText(dlpath)
		self.dlPathBtn.setToolTip(dlpath)

		self.vtable.setColumnWidth(0, 50)
		self.vtable.setColumnWidth(1, 150)
		self.vtable.setColumnWidth(2, 50)
		self.vtable.setColumnWidth(4, 180)
		self.vtable.setColumnWidth(5, 50)

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
		self.vPageAction.triggered.connect(lambda: self.changePage(1))
		self.pPageAction.triggered.connect(lambda: self.changePage(2))
		self.fPageAction.triggered.connect(lambda: self.changePage(2))
		self.exitAction.triggered.connect(QCoreApplication.quit)
		
		# 设置菜单下 Action
		self.minSizeAction.triggered.connect(self.modifyMinSize)
		self.bgiPathAction.triggered.connect(self.modifyBGIPath)
		self.downloadPathaction.triggered.connect(self.modifyDLPath)

		# 关于下的 Action
		self.authorAction.triggered.connect(lambda: QDesktopServices.openUrl(QUrl('https://github.com/LewisTian')))
		self.appAction.triggered.connect(lambda: QDesktopServices.openUrl(QUrl('https://github.com/LewisTian/bili-box')))

		# 按钮
		self.searchBtn.clicked.connect(self.resolveInput)
		self.dlPathBtn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(self.dlpath)))
		self.v2homeBtn.clicked.connect(self.toHome)
		self.vdownloadBtn.clicked.connect(self.download)
		self.dlAllBox.clicked.connect(self.isAllDownload)

	def changePage(self, index):
		'''修改当前页'''
		if  0 < index < 3: self.stackedWidget.setCurrentIndex(index)

	def setLogo(self):
		'''根据季节来更换logo(当前只有秋冬的;3)'''
		month = datetime.datetime.now().month
		if 3 <= month <= 5:
			pass
		elif 6 <= month <= 8:
			pass
		elif 9 <= month <= 11:
			self.logo.setPixmap(QPixmap('images/bili-autumn.png'))
			self.logo.setToolTip('嗶哩嗶哩秋~')
		else:
			self.logo.setPixmap(QPixmap('images/bili-winter.png'))
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
		self.dlPathBtn.setText(dlpath)
		self.dlPathBtn.setToolTip(dlpath)

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
				return
			self.request(index)
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
			# zz = 'page":(.*?),"from":"vupload","part":"(.*?)","duration":'
			# links = re.findall(zz, r.text)
			# print(links)
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
				pass
			url = f'http://api.bilibili.com/x/space/fav/arc?vmid={self.mid}&ps=30&fid={self.fid}&tid=0&keyword=&pn={1}&order=fav_time&jsonp=jsonp'
			print(url)
			try:
				r = requests.get(url, headers=fheaders).json()
			except Exception as e:
				print(e)
				return
			print(r)
		else:
			pass
			
	
	def resolveInfoDone(self, btype, info):
		'''解析线程完成返回相关信息
		btype 类型 1 => 视频 2=> 图片
		1: info：序号 分p标题 标题 时长 大小 链接
		2: info 列表：[description, upload_time, view_count, collect_count, like_count, pics]
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
		else:
			pass

		self.vlists.append(info[-1])

	def resolveUserInfoDone(self, info):
		pix = QPixmap(info[1])
		self.pavator.setPixmap(pix)
		self.pavator.setScaledContents(True)
		self.pavator.setToolTip(info[0])
		self.pname.setText(info[0])

	def errorHappened(self):
		QMessageBox.warning(self, '嗶哩嗶哩盒子©Lewis Tian', '发生了一个错误，请重试...', QMessageBox.Ok)

	def toHome(self):
		'''回首页'''
		self.stackedWidget.setCurrentIndex(0)

	def isAllDownload(self):
		'''是否下载全部视频'''
		if self.dlAllBox.isChecked():
			self.vtable.setRangeSelected(
					QTableWidgetSelectionRange(0, 0, 
						self.vtable.rowCount()-1, self.vtable.columnCount()-1), 
					True)

	def download(self):
		'''分发下载视频视频'''
		rows = [x for x in range(self.vtable.rowCount()) if self.vtable.item(x, 0).isSelected()]
		if not rows: return
		for x in rows[::-1]:
			val = self.vtable.cellWidget(x, 4).value()
			if val == 100: rows.remove(x)
		self.vDownlaod.num = rows
		self.vDownlaod.urls = [self.vlists[x] for x in rows]
		self.vDownlaod.start()

	def updateProgress(self, row, percent):
		'''更新进度条'''
		self.vtable.cellWidget(row, 4).setValue(percent)

	def updateSlice(self, row, p):
		slices = self.vtable.item(row, 5).text().split('/')[1]
		self.vtable.setItem(row, 5, QTableWidgetItem(f'{p}/{slices}'))

class VideoRetrieval(QThread):
	'''获取视频下载链接'''
	done = pyqtSignal(int, list)
	error = pyqtSignal()
	def __init__(self):
		super(VideoRetrieval, self).__init__()

	def run(self):		
		url = f'https://www.bilibili.com/video/av{self.key}'
		r = requests.get(url, headers = headers).text
		title = re.findall(r'<h1 title="(.*?)">', r)[0].replace(' ','-')
		self.title = title
		cover = re.findall(r'<meta.*?itemprop="image" content="(.*?)"/><meta', r)
		self.cover = cover
		pages = re.findall(r'page":(.*?),"from":"vupload","part":"(.*?)","duration":', r) 
		if not pages:
			'''可能是番剧、电影啥的无法解析出来'''
			self.error.emit()
		with futures.ThreadPoolExecutor(32) as executor:
			executor.map(self.resolve, pages)

	def resolve(self, page):
		'''获取每个分p的视频链接
		page: (index, page title)
		'''
		url = f'https://www.bilibili.com/video/av{self.key}?p={page[0]}'
		r = requests.get(url, headers=headers).text
		regex = '"order":(.*?),"length":(.*?),"size":(.*?),.*?"url":"(.*?)"'
		result = re.findall(regex, r) # 序号 时长 大小 链接
		time = str(sum([int(i[1]) for i in result])//60000) +":"+str(int((sum([int(i[1]) for i in result])%60000)//1000))
		size = round(sum([int(i[2]) for i in result])/1024/1024, 1)
		url = [i[3] for i in result]
		ret = list(page) + [self.title, time, size, url] # [类型] 序号 分p标题 标题 时长 大小 链接
		self.done.emit(1, ret)

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
			print(f'path: {folder}/{filename}')
			if not os.path.exists(folder):
				os.mkdir(folder)
			urequest.urlretrieve(j, filename=f'{folder}/{filename}', reporthook=self.report)
			self.updateSlice.emit(int(threading.current_thread().name), str(i+1))
		if len(url) > 1:
			self.merge(folder)
		
	def report(self, count, blockSize, totalSize):
		downloadedSize = count * blockSize
		percent = int(downloadedSize * 100 / totalSize)
		if not self.percent == percent:
			self.percent = percent
			self.updateProgress.emit(int(threading.current_thread().name), percent)

	def merge(self, folder):
		files = glob(folder+'/*.flv')
		outlists = []
		for i, x in enumerate(files):
			outfile = f'{folder}/{i}.ts'
			outlists.append(outfile)
			print(x, outfile)
			s = f'ffmpeg.exe -i {x} -vcodec copy -acodec copy -vbsf h264_mp4toannexb {outfile}'
			os.system(s)
		s = f'''ffmpeg.exe -i "concat:{'|'.join(outlists)}" -acodec copy -vcodec copy -absf aac_adtstoasc {folder}/{folder}.mp4'''
		os.system(s)
		for x in outlists:
			os.remove(x)

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