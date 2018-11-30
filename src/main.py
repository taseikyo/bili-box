#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2018-11-29 19:04:30
# @Author  : Lewis Tian (chtian@hust.edu.cn)
# @Link    : https://lewistian.github.io
# @Version : Python3.7

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from mwin import Ui_MWin
from concurrent import futures
import sys
import os
import shutil
import time
import datetime
import requests
import re

MAX_WIDTH = 1920
MAX_HEIGHT = 1080

headers = {
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
	'Cookie': 'CURRENT_QUALITY=64; DedeUserID=227050458; '
}

class MWin(QMainWindow, Ui_MWin):
	'''嗶哩嗶哩盒子'''
	def __init__(self, parent=None):
		super(MWin, self).__init__(parent)
		self.setupUi(self)
		try:
			with open('style.qss') as f: 
				style = f.read() # 读取样式表
				self.setStyleSheet(style)
		except:
			print("open stylesheet error")

		# 变量
		self.mFlag = False
		self.mPosition = None
		self.bgiPath = '' # 背景图片的路径
		self.key = None # 视频链接 id
		self.vRetrieval = VideoRetrieval()

		self.setLogo()
		self.setBackgroundImage(self.bgiPath)
		self.connectSlots()

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
			print(ext)
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

	def connectSlots(self):
		'''关联所有信号槽'''
		# 设置菜单下 Action
		self.minSizeAction.triggered.connect(self.modifyMinSize)
		self.bgiPathAction.triggered.connect(self.modifyBGIPath)

		# 关于下的 Action
		self.authorAction.triggered.connect(lambda: QDesktopServices.openUrl(QUrl('https://github.com/LewisTian')))
		self.appAction.triggered.connect(lambda: QDesktopServices.openUrl(QUrl('https://github.com/LewisTian/bili-box')))

		# 按钮
		self.searchBtn.clicked.connect(self.resolveInput)

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
			template1 = f'        MWin.setMinimumSize(QtCore.QSize({x}, {y}))\n'
			template2 = f'        MWin.resize({x}, {y})\n'
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

	def resolveInput(self):
		index = self.comboBoxHome.currentIndex()
		text = self.lineEditHome.text()
		if text.strip(' ') == '':
			return
		if index == 0:
			key = re.findall(r'av(\d+)', text)[0]
			if not key: return
			if self.key and self.key == key:
				'''避免重复请求'''
				return
			self.key = key
			self.request()
			# self.vRetrieval.url = f'https://www.bilibili.com/video/av{self.key}'
			# self.vRetrieval.start()
		elif index == 1:
			pass
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
			pass
		else:
			pass
	
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