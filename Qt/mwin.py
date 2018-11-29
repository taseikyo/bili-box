# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mwin.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MWin(object):
    def setupUi(self, MWin):
        MWin.setObjectName("MWin")
        MWin.resize(720, 405)
        MWin.setMinimumSize(QtCore.QSize(720, 405))
        font = QtGui.QFont()
        font.setFamily("Microsoft YaHei")
        font.setPointSize(10)
        MWin.setFont(font)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/images/bililogo"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MWin.setWindowIcon(icon)
        MWin.setIconSize(QtCore.QSize(35, 35))
        self.centralWidget = QtWidgets.QWidget(MWin)
        self.centralWidget.setObjectName("centralWidget")
        MWin.setCentralWidget(self.centralWidget)
        self.statusBar = QtWidgets.QStatusBar(MWin)
        self.statusBar.setObjectName("statusBar")
        MWin.setStatusBar(self.statusBar)
        self.menuBar = QtWidgets.QMenuBar(MWin)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 720, 23))
        self.menuBar.setObjectName("menuBar")
        MWin.setMenuBar(self.menuBar)

        self.retranslateUi(MWin)
        QtCore.QMetaObject.connectSlotsByName(MWin)

    def retranslateUi(self, MWin):
        _translate = QtCore.QCoreApplication.translate
        MWin.setWindowTitle(_translate("MWin", "嗶哩嗶哩盒子©Lewis Tian"))

import res_rc
