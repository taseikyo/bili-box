#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2018-11-29 19:04:30
# @Author  : Lewis Tian (chtian@hust.edu.cn)
# @Link    : https://lewistian.github.io
# @Version : Python3.7

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys
import os
import time
import datetime
from mwin import Ui_MWin


MAX_WIDTH = 1920
MAX_HEIGHT = 1080

class MWin(QMainWindow, Ui_MWin):
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
		self.bgmPath = '' # 背景图片的路径

		self.setLogo()
		self.setBackgroundImage()
		self.connectSlots()

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

	def setBackgroundImage(self, path='images/background.jpg'):
		'''设置主窗口的背景图片'''
		# self.setStyleSheet(f'border-image: url({path});')
		self.bgmPath = path
		self.setAutoFillBackground(True)
		pal = self.palette()
		# pal.setBrush(self.backgroundRole(), QPixmap(f'{path}'))
		pixmap = QPixmap(f'{path}').scaled(self.size())
		pal.setBrush(QPalette.Background, QBrush(pixmap))
		self.setPalette(pal)

	def resizeEvent(self, event):
		'''窗口大小改变，背景图的大小也要改变
		因为设置时已经定死了图片的尺寸'''
		self.setBackgroundImage(self.bgmPath)

	def connectSlots(self):
		'''关联所有信号槽'''
		# 设置菜单下 Action
		self.minSizeAction.triggered.connect(self.minSizeActionFunc)
		self.bgmPathAction.triggered.connect(self.bgmPathActionFunc)

		# 关于下的 Action
		self.authorAction.triggered.connect(lambda: QDesktopServices.openUrl(QUrl('https://github.com/LewisTian')))
		self.appAction.triggered.connect(lambda: QDesktopServices.openUrl(QUrl('https://github.com/LewisTian/bili-box')))

	def minSizeActionFunc(self):
		'''修改窗口的最小尺寸（默认是(960, 540)）'''
		text, okPressed = QInputDialog.getText(self, '修改窗口尺寸', '输入尺寸:', QLineEdit.Normal, "输入两个数字 以空格分割")
		if okPressed and text != '':
			raw = text.split(' ')
			try:
				x, y = int(raw[0]), int(raw[1])
			except:
				return
			self.setMinimumSize(x, y)
			print(f'{os.getcwd()}/mwin.py')
			try:
				with open(f'{os.getcwd()}/mwin.py', encoding='utf-8') as f:
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


	def bgmPathActionFunc(self):
		pass

	def mousePressEvent(self, event):
		x = (event.globalPos() - self.pos()).x()
		y = (event.globalPos() - self.pos()).y()
		if event.button() == Qt.LeftButton:
			self.mFlag = True
			self.mPosition = event.globalPos() - self.pos()
			event.accept()
			# self.setCursor(QCursor(Qt.OpenHandCursor))
	
	def mouseMoveEvent(self, QMouseEvent):
		if Qt.LeftButton and self.mFlag:  
			self.move(QMouseEvent.globalPos() - self.mPosition)
			QMouseEvent.accept()
			
	def mouseReleaseEvent(self, QMouseEvent):
		self.mFlag = False

def mainSplash():
	app = QApplication(sys.argv)
	splash = QSplashScreen(QPixmap('../images/background.jpg'))
	splash.showMessage("启动界面", Qt.AlignLeft | Qt.AlignBottom, Qt.black)
	splash.show()
	time.sleep(2)
	app.processEvents()
	window = QWidget()
	window.show()
	splash.finish(window)
	del splash
	app.exec()

if __name__ == '__main__':
	app = QApplication(sys.argv)
	w = MWin()
	w.show()
	sys.exit(app.exec_())