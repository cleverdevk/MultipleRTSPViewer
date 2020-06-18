from threading import Thread
import time
from PyQt5.QtWidgets import *
from PyQt5 import QtCore
from PyQt5 import *
import sys
import cv2
from xml.etree.ElementTree import parse, Element, dump, ElementTree, XML


class cctvManageApp(QWidget):
    def __init__(self, main):
        super().__init__()
        self.cb = QComboBox(self)
        self.tree = None
        self.root = None
        self.sites = None
        self.idx = 0
        self.names = list()
        self.uris = list()
        self.tb = QTableWidget(self)
        self.addURIBtn = QPushButton(self)
        self.delURIBtn = QPushButton(self)
        self.mainWidget = main
        self.addURIBtn.clicked.connect(self.onClickAdd)
        self.delURIBtn.clicked.connect(self.onClickRemove)
        self.cb.activated.connect(self.onActivated)

    def initUI(self):
        self.cb.clear()

        self.setWindowTitle("CCTV 관리")
        self.move(400,400)
        self.resize(600,500)

        self.initXmlData()

        self.cb.addItems(self.names)


        self.tb.resize(500, 400)
        self.tb.setRowCount(len(self.uris[0]))
        self.tb.setColumnCount(1)
        self.setTableData(0)
        self.tb.move(0,50)
        self.tb.setHorizontalHeaderLabels(['URI'])

        self.addURIBtn.setText("CCTV 추가")
        self.addURIBtn.move(500, 470)


        self.delURIBtn.setText("CCTV 삭제")
        self.delURIBtn.move(420, 470)


    def onClickRemove(self):
        reply = QMessageBox.question(self, "URI 삭제", "진짜로 삭제하시겠습니까?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            r = self.tb.currentRow()
            selectedUri = self.tb.item(r, 0)
            node = self.tree.find('.//site[@name="' + self.names[self.idx] + '"]')

            for uri_node in node.findall("uri"):
                print(uri_node.text)
                if selectedUri.text() == uri_node.text:
                    node.remove(uri_node)
                    ElementTree(self.root).write("config.xml")
                    self.initXmlData()
                    self.setTableData(self.idx)
                    break


    def onClickAdd(self):
        text, ok = QInputDialog.getText(self,"CCTV 추가", "CCTV URI : ")
        if ok:
            node = self.tree.find('.//site[@name="' + self.names[self.idx] + '"]')
            newNode = Element("uri")
            newNode.text = text

            node.append(newNode)
            dump(self.root)

            ElementTree(self.root).write("config.xml")
            self.initXmlData()
            self.setTableData(self.idx)

    def setTableData(self, i):
        self.tb.clear()
        self.tb.setRowCount(len(self.uris[i]))
        for j in range(0, len(self.uris[i])):
            item = QTableWidgetItem(self.uris[i][j])
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.tb.setItem(j,0, item)
            self.tb.resizeColumnsToContents()
            self.tb.resizeRowsToContents()


    def initXmlData(self):
        self.names.clear()
        self.uris.clear()
        self.tree = parse('config.xml')
        self.root = self.tree.getroot()
        self.sites = self.root.findall('site')
        for x in self.sites:
            self.names.append(x.attrib['name'])
            u = [y.text for y in x.findall('uri')]
            self.uris.append(u)

        print(self.names)
        print(self.uris)

    def onActivated(self, index):
        print(index)
        self.idx = index
        self.setTableData(index)

    def closeEvent(self, QCloseEvent):
        print("close called")
        QApplication.sendEvent(self.mainWidget, QCloseEvent)




class MyApp(QWidget):
    def event(self, ev):
        if ev.type() == QGestureEvent.Close:
            self.initXmlData()
        return super().event(ev)

    def __init__(self):
        super().__init__()
        self.idx = 0
        self.names = list()
        self.uris = list()

        self.tree = None
        self.root = None
        self.sites = None

        self.width = 0
        self.height = 0

        self.cctvWindow = cctvManageApp(self)

        self.cb = QComboBox(self)
        self.installEventFilter(self)
        self.cb.activated.connect(self.onActivated)

        self.initUI()


    def initXmlData(self):
        self.names.clear()
        self.uris.clear()
        self.tree = parse('config.xml')
        self.root = self.tree.getroot()
        self.sites = self.root.findall('site')
        for x in self.sites:
            self.names.append(x.attrib['name'])
            u = [y.text for y in x.findall('uri')]
            self.uris.append(u)

        print(self.names)
        print(self.uris)

    def onDoubleClicked(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDBLCLK:
            print("Double Clicked")
            _,_,w,h = cv2.getWindowImageRect(param[0])
            if w == 500 and h == 350:
                cv2.resizeWindow(param[0], self.width, self.height)
                cv2.moveWindow(param[0], 0,0)
            else:
                cv2.resizeWindow(param[0], 500, 350)
                print(param)
                cv2.moveWindow(param[0], param[1], param[2])



    def viewCCTV(self):
        caps = list()
        windowNames = list()
        startX, startY = 0, 0
        for uri in (self.uris[self.idx]):
            c = cv2.VideoCapture(uri)
            if c.isOpened():
                print("add")
                caps.append(c)
            else:
                print("don't add")
                continue
            #caps.append(cv2.VideoCapture(uri))
            winname = 'Camera ' + uri
            windowNames.append(winname)
            cv2.namedWindow(winname)
            cv2.moveWindow(winname, startX, startY)
            cv2.resizeWindow(winname, 500, 350)
            cv2.setMouseCallback(winname, self.onDoubleClicked, (winname,startX,startY))
            startX += 500
            if startX + 500 > self.width:
                startX = 0
                startY += 350
            #cv2.resizeWindow(winname, 200, 200)
        finish = False
        while True:
            for i in range(0, len(caps)):
                _, frame = caps[i].read()
                if frame is None:
                    continue
                x,y,w,h = cv2.getWindowImageRect(windowNames[i])
                resized_frame = cv2.resize(frame, (w,h))
                cv2.imshow(windowNames[i], resized_frame)

                k = cv2.waitKey(1) & 0xFF
                if k == 27:
                    caps[i].release()
                    finish = True
                    break
            if finish:
                break

        for name in windowNames:
            cv2.destroyWindow(name)

    def onActivated(self, index):
        self.idx = index

    def addsite(self):
        text, ok = QInputDialog.getText(self,"사이트 추가", "사이트 이름 : ")
        if ok:
            newNode = Element("site", name=text)

            self.root.append(newNode)
            dump(self.root)

            ElementTree(self.root).write("config.xml")

            self.initUI()

    def addcctv(self):
        self.cctvWindow.initUI()
        self.cctvWindow.show()


    def initUI(self):
        self.width, self.height = self.screen().geometry().width(), self.screen().geometry().height()

        self.initXmlData()
        self.cb.clear()
        lbl = QLabel("사이트 선택",self)
        lbl.move(50,30)

        #cb = QComboBox(self)
        self.cb.addItems(self.names)
        self.cb.move(50,50)


        btn = QPushButton(self)
        btn.setText("CCTV 보기")
        btn.move(50, 150)
        btn.clicked.connect(self.viewCCTV)


        btn_add_site = QPushButton(self)
        btn_add_site.setText("사이트 추가")
        btn_add_site.move(150,150)
        btn_add_site.clicked.connect(self.addsite)

        btn_add_cctv = QPushButton(self)
        btn_add_cctv.setText("CCTV 관리")
        btn_add_cctv.move(230,150)
        btn_add_cctv.clicked.connect(self.addcctv)

        self.setWindowTitle("제주 CCTV 뷰어")
        self.move(300,300)
        self.resize(400,200)
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    sys.exit(app.exec_())
