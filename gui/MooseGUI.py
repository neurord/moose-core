# used to parse files more easily
from __future__ import with_statement

#numerical computations
import numpy as np

# for command-line arguments
import sys
import os
import sys
import subprocess
from datetime import date

#moose imports
import moose
import moose.utils as mooseUtils
from collections import defaultdict
from objectedit import ObjectFieldsModel, ObjectEditView
from moosehandler import MooseHandler
from mooseplot import MoosePlot,MoosePlotWindow
import kineticlayout

from filepaths import *
from defaults import *

# Qt4 bindings for Qt
from PyQt4 import QtCore,QtGui
from PyQt4.QtCore import QEvent, Qt

# import the MainWindow widget from the converted .ui (pyuic4) files
from newgui import Ui_MainWindow

import config


class DesignerMainWindow(QtGui.QMainWindow, Ui_MainWindow):
    """Customization for Qt Designer created window"""
    def __init__(self, interpreter=None,parent = None):
        # initialization of the superclass
        super(DesignerMainWindow, self).__init__(parent)
        # setup the GUI --> function generated by pyuic4
        self.objFieldEditorMap = {}
        self.setupUi(self)
        self.setCorner(Qt.BottomRightCorner,Qt.RightDockWidgetArea)
        self.setCorner(Qt.BottomLeftCorner,Qt.LeftDockWidgetArea)
        self.mooseHandler = MooseHandler()

        #other variables
        self.currentTime = 0.0

        #plot variables
        self.plotConfigCurrentSelection = None
        self.plotConfigAcceptPushButton.setEnabled(False)
        self.plotWindowFieldTableDict = {} #moosePlotWinName:[mooseTable]
        self.plotWinNamePlotDict = {} #moosePlotWinName:mooseplot

        #do not show other docks
        self.defaultDockState()

        #connections
        self.connectElements()

    def defaultDockState(self):
        #this will eventually change corresponding to the "mode" of operation - Edit/Plot/Run
        self.moosePopulationEditDock.setVisible(False)
        self.mooseLibraryDock.setVisible(False)
        self.mooseConnectDock.setVisible(False)

        self.menuHelp.setEnabled(False)
        self.menuView.setEnabled(False)
        self.menuClasses.setEnabled(False)

    def connectElements(self):
        #gui connections
        self.connect(self.actionLoad_Model,QtCore.SIGNAL('triggered()'), self.popupLoadModelDialog)
        self.connect(self.actionQuit,QtCore.SIGNAL('triggered()'),self.doQuit)
        #plotdock connections
        self.connect(self.plotConfigAcceptPushButton,QtCore.SIGNAL('pressed()'),self.addFieldToPlot)
        self.connect(self.plotConfigNewWindowPushButton,QtCore.SIGNAL('pressed()'),self.plotConfigAddNewPlotWindow)
        #internal connections
        self.connect(self.mooseHandler, QtCore.SIGNAL('updatePlots(float)'), self.updatePlots)

    def popupLoadModelDialog(self):
        fileDialog = QtGui.QFileDialog(self)
        fileDialog.setToolTip("<font color='blue'> Select a model Neural / KKit to open. Try Mitral.g / Kholodenko.g from DEMOS> mitral-ee / kholodenko folders </font>")
        fileDialog.setFileMode(QtGui.QFileDialog.ExistingFile)
        ffilter = ''
        for key in sorted(self.mooseHandler.fileExtensionMap.keys()):
            ffilter = ffilter + key + ';;'
        ffilter = ffilter[:-2]
        fileDialog.setFilter(self.tr(ffilter))
        # The following version gymnastic is because QFileDialog.selectNameFilter() was introduced in Qt 4.4
        if (config.QT_MAJOR_VERSION > 4) or ((config.QT_MAJOR_VERSION == 4) and (config.QT_MINOR_VERSION >= 4)):
            for key, value in self.mooseHandler.fileExtensionMap.items():
                if value == MooseHandler.type_genesis:
                    fileDialog.selectNameFilter(key)
                    break
        targetPanel = QtGui.QFrame(fileDialog)
        targetPanel.setLayout(QtGui.QVBoxLayout())
        #targetTree = MooseTreeWidget(fileDialog)
        currentPath = self.mooseHandler._current_element.path
        
        #for item in targetTree.itemList:
         #   if item.getMooseObject().path == currentPath:
          #      targetTree.setCurrentItem(item)
        targetLabel = QtGui.QLabel('Target Element')
        targetText = QtGui.QLineEdit(fileDialog)

        targetText.setText(currentPath)
        targetText.setText('/dummy')
        targetPanel.layout().addWidget(targetLabel)
        targetPanel.layout().addWidget(targetText)
        layout = fileDialog.layout()
        #layout.addWidget(targetTree)
        layout.addWidget(targetPanel)
        #self.connect(targetTree, QtCore.SIGNAL('itemClicked(QTreeWidgetItem *, int)'), lambda item, column: targetText.setText(item.getMooseObject().path))
        if fileDialog.exec_():
            fileNames = fileDialog.selectedFiles()
            fileFilter = fileDialog.selectedFilter()
            fileType = self.mooseHandler.fileExtensionMap[str(fileFilter)]
            directory = fileDialog.directory() # Potential bug: if user types the whole file path, does it work? - no but gives error message
            #self.statusBar.showMessage('Loading model, please wait')
            
            app = QtGui.qApp
            app.setOverrideCursor(QtGui.QCursor(Qt.BusyCursor)) #shows a hourglass - or a busy/working arrow
            for fileName in fileNames:
                #print ": filename",str(fileName),str(fileType),str(targetText.text())
                modeltype  = self.mooseHandler.loadModel(str(fileName), str(fileType), str(targetText.text()))
                modelpath = str(targetText.text())
                
                if modeltype == MooseHandler.type_kkit:
                    try:
                        self.addLayoutWindow(modelpath)
                        self.actionLoad_Model.setEnabled(0) #to prevent multiple loads
                        
                    except kineticlayout.Widgetvisibility:
                        print 'No kkit layout for: %s' % (str(fileName))
                    #self.populateKKitPlots()
                #self.populateDataPlots()
                #self.updateDefaultTimes(modeltype)
            #self.modelTreeWidget.recreateTree()
            #self.enableControlButtons()
            #self.checkModelType()
            print 'Loaded model',  fileName, 'of type', modeltype
            app.restoreOverrideCursor()

    def resizeEvent(self, event):
        QtGui.QWidget.resizeEvent(self, event)

    def addLayoutWindow(self,modelpath):
        centralWindowsize =  self.layoutWidget.size()
        layout = QtGui.QHBoxLayout(self.layoutWidget)
        self.sceneLayout = kineticlayout.kineticsWidget(centralWindowsize,modelpath,self.layoutWidget)
        self.sceneLayout.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding))
        self.connect(self.sceneLayout, QtCore.SIGNAL("itemDoubleClicked(PyQt_PyObject)"), self.makeObjectFieldEditor)
        layout.addWidget(self.sceneLayout)
        self.layoutWidget.setLayout(layout)
        self.sceneLayout.show()

        #objectEditor related
    def refreshObjectEditor(self,item,number):
        self.makeObjectFieldEditor(item.getMooseObject())

    def makeObjectFieldEditor(self, obj):
        if obj.class_ == 'Shell' or obj.class_ == 'PyMooseContext' or obj.class_ == 'GenesisParser':
            print '%s of class %s is a system object and not to be edited in object editor.' % (obj.path, obj.class_)
            return
        try:
            self.objFieldEditModel = self.objFieldEditorMap[obj.getId()]
        except KeyError:
            self.objFieldEditModel = ObjectFieldsModel(obj)
            self.objFieldEditorMap[obj.getId()] = self.objFieldEditModel

        self.mTable.setObjectName(str(obj.getId()))
        self.mTable.setModel(self.objFieldEditModel)
        if hasattr(self, 'sceneLayout'):
            self.connect(self.objFieldEditModel,QtCore.SIGNAL('objectNameChanged(PyQt_PyObject)'),self.sceneLayout.updateItemSlot)
        self.updatePlotDockFields(obj)

        #plots related 
    def updatePlots(self,currentTime):
        #updates plots every update_plot_dt time steps see moosehandler.
        for plotWinName,plot in self.plotWinNamePlotDict.iteritems():
            plot.updatePlot(currentTime)
        self.updateCurrentTime(currentTime)

    def updatePlotDockFields(self,obj):
        #add plot-able elements according to predefined  
        self.plotConfigCurrentSelectionLabel.setText(obj.getField('name'))
        fieldType = obj.getField('class')
        self.plotConfigCurrentSelectionTypeLabel.setText(fieldType)
        self.plotConfigFieldSelectionComboBox.clear()
        try: 
            self.plotConfigFieldSelectionComboBox.addItems(PLOT_FIELDS[fieldType])
            self.plotConfigCurrentSelection = obj
            self.plotConfigAcceptPushButton.setEnabled(True)
        except KeyError:
            #undefined field - see PLOT_FIELDS variable in defaults.py
            self.plotConfigFieldSelectionComboBox.clear()
            self.plotConfigCurrentSelection = None
            self.plotConfigAcceptPushButton.setEnabled(False)
            
    def addFieldToPlot(self):
        #creates tables - called when 'Okay' pressed in plotconfig dock
        dataNeutral = moose.Neutral(self.plotConfigCurrentSelection.getField('path')+'/data')
        newTable = moose.Table(self.plotConfigCurrentSelection.getField('path')+'/data'+str(self.plotConfigFieldSelectionComboBox.currentText()))
        moose.connect(newTable,'requestData',self.plotConfigCurrentSelection,'get_'+str(self.plotConfigFieldSelectionComboBox.currentText()))

        if str(self.plotConfigWinSelectionComboBox.currentText()) in self.plotWindowFieldTableDict:
            #case when plotwin already exists - append new table to mooseplotwin
            self.plotWindowFieldTableDict[str(self.plotConfigWinSelectionComboBox.currentText())].append(newTable)
            #select the corresponding plot (mooseplot) from the plotwindow (mooseplotwindow) 
            plot = self.plotWinNamePlotDict[str(self.plotConfigWinSelectionComboBox.currentText())] 
            
            #do not like the legends shown in the plots, change the field 2 below
            plot.addTable(newTable,newTable.getField('path'))
        else:
            #no previous mooseplotwin - so create now, and add table to corresp dict
            self.plotWindowFieldTableDict[str(self.plotConfigWinSelectionComboBox.currentText())] = [newTable]
            plotWin = MoosePlotWindow(self)
            plotWin.setWindowTitle(str(self.plotConfigWinSelectionComboBox.currentText()))

            plot = MoosePlot(plotWin)
            #fix sizing! - somethign is wrong here. plot doesnt resize with plotwin
            sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(plot.sizePolicy().hasHeightForWidth())
            plot.setSizePolicy(sizePolicy)

            #do not like the legends shown in the plots, change the field 2 below
            plot.addTable(newTable,newTable.getField('path'))
            plotWin.show()
            #create a new Dictionary entry of plotWindowName:plot
            self.plotWinNamePlotDict[str(self.plotConfigWinSelectionComboBox.currentText())]=plot 

    def plotConfigAddNewPlotWindow(self):
        #called when new plotwindow pressed in plotconfig dock
        count = self.plotConfigWinSelectionComboBox.count()
        self.plotConfigWinSelectionComboBox.addItem('Plot Window '+str(count+1))
        self.plotConfigWinSelectionComboBox.setCurrentIndex(count)
        
        #general
    def updateCurrentTime(currentTime):
        self.currentTime = currentTime

    def doQuit(self):
        QtGui.qApp.closeAllWindows()


# create the GUI application
app = QtGui.QApplication(sys.argv)
# instantiate the main window
dmw = DesignerMainWindow()
# show it
dmw.show()
# start the Qt main loop execution, exiting from this script
#http://code.google.com/p/subplot/source/browse/branches/mzViewer/PyMZViewer/mpl_custom_widget.py
#http://eli.thegreenplace.net/files/prog_code/qt_mpl_bars.py.txt
#http://lionel.textmalaysia.com/a-simple-tutorial-on-gui-programming-using-qt-designer-with-pyqt4.html
#http://www.mail-archive.com/matplotlib-users@lists.sourceforge.net/msg13241.html
# with the same return code of Qt application
sys.exit(app.exec_())
