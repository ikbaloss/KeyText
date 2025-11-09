from PyQt5 import QtCore, QtGui, QtWidgets

import os, re, sys
 
from collections import Counter, defaultdict


import xlsxwriter

#import subprocess

import pandas as pd
import collections
import numpy as np
import string
import gensim
from gensim.models import Word2Vec



from datetime import datetime, timedelta
import matplotlib.dates as mdates

#import webbrowser

import networkx as nx

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.ticker as mticker
import matplotlib.cm as cm
from matplotlib.colors import ListedColormap
       

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5.QtWidgets import QGridLayout, QFileDialog, QMainWindow, QSpinBox, QMessageBox, \
    QItemDelegate, QVBoxLayout, QHBoxLayout, QSizePolicy, QTabWidget, QApplication, \
        QTableView, QStatusBar, QMenu, QPushButton, QLabel, QComboBox, QMenuBar, \
        QAbstractItemView, QListWidget, QRadioButton, QLineEdit, QInputDialog,\
        QDialog, QDialogButtonBox, QCheckBox, QScrollArea, QWidget

from PyQt5.QtGui import QBrush, QColor

from PyQt5.QtCore import QAbstractTableModel, Qt 

from wordcloud import WordCloud

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx
from itertools import combinations
import community as community_louvain
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import pdist
from anytree import Node, RenderTree

# Creating the main window 
class App(QMainWindow): 
    def __init__(self): 
        super().__init__() 
        self.title = "KeyText Version 0.16"
        self.left = 50
        self.top = 50
        self.width = 800
        self.height = 600

        self.main_data = pd.DataFrame()
        
        #N-grams
        self.unigrams = pd.DataFrame()
        self.bigrams = pd.DataFrame()
        self.trigrams = pd.DataFrame()
        self.fourgrams = pd.DataFrame()
        self.fivegrams = pd.DataFrame()
        
        self.just_refresh = False 
        
        self.main_data_hasbeen_changed = False
        self.useDate = False
        #self.cleaned_data = ''
        self.stop_words = ''
        
        self.non_duplicate_data = pd.DataFrame()
        self.Indonesia = True
        
        #time series data for plotting
        #self.df_selected_data_value = pd.DataFrame()
        self.df_date = pd.DataFrame()
        self.df_datafile = pd.DataFrame()
        
        #kd = open("katadasar.txt", "r")
        #content = kd. read()
        self.kamus = []
                
        self.list_of_DataFiles = []
        
        self.main_data_hasbeen_changed = False
        self.main_data_hastobe_saved = False
        
        self.msgBox = QMessageBox()

        self.setWindowTitle(self.title) 
        self.setGeometry(self.left, self.top, self.width, self.height) 
  
        self.tab_widget = MyTabWidget(parent=self) 
        self.setCentralWidget(self.tab_widget) 
  
        self.show() 
        
        
        self.statusbar = QStatusBar()
        
        self.setStatusBar(self.statusbar)
        
        self.menubar = QMenuBar()
        
        self.menuFiles = QMenu()
        self.menuFiles.setTitle("File")
        
        self.setMenuBar(self.menubar)
        self.actionOpen = QtWidgets.QAction()
        self.actionOpen.setText("Open")
        self.actionOpen.triggered.connect(self.openFile)
        
        self.actionSave = QtWidgets.QAction()
        self.actionSave.setText("Save")
        self.actionSave.triggered.connect(self.saveData)
        
        self.actionRefresh = QtWidgets.QAction()
        self.actionRefresh.setText('Refresh')
        self.actionRefresh.triggered.connect(self.refreshWV)
        
        self.actionExit = QtWidgets.QAction()
        self.actionExit.setText("Exit")
        self.actionExit.triggered.connect(self.exitApp)
        
        self.menuFiles.addAction(self.actionOpen)
        #self.menuFiles.addAction(self.actionOpenCleanedData)
        self.menuFiles.addAction(self.actionSave)
        self.menuFiles.addAction(self.actionRefresh)
        self.menuFiles.addAction(self.actionExit)
        self.menubar.addAction(self.menuFiles.menuAction())
    
    
    def fill_unigrams(self):
        # Step 1: Combine all comments into a single string
        text = " ".join(self.main_data['SelectedColumn'].dropna().astype(str).tolist())
        
        # Step 2: Tokenize into words (basic whitespace + punctuation removal)
        tokens = re.findall(r'\b\w+(?:[-_]\w+)*\b', text.lower())  # convert to lowercase and extract words
        
        # Step 3: Count unigrams using Counter
        unigram_freq = Counter(tokens)
        
        # Step 4: Convert to DataFrame
        self.unigrams = pd.DataFrame(unigram_freq.items(), columns=['Unigram', 'Frequency'])
        
        # Step 5: Sort by frequency (optional)
        self.unigrams = self.unigrams.sort_values(by='Frequency', ascending=False).reset_index(drop=True)
        
        # Now unigrams contains the result
        print(self.unigrams.head())
        
 
    def exitApp(self):
        if self.main_data_hastobe_saved:
            reply = QMessageBox.question(self, "Exit Confirmation",
                                     "Do you want to save your changes before exiting?",
                                     QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                                     QMessageBox.Yes)

        if reply == QMessageBox.Yes:
            self.saveData()
            #print("Saving file...")
            self.close()
        elif reply == QMessageBox.Cancel:
            return  # Prevent window closing
        else:
            self.close()
        
    def refreshWV(self):
        if self.main_data_hasbeen_changed:
            self.just_refresh = True
            self.tab_widget.tabRawData.selectColumns()
            self.main_data_hasbeen_changed = False
            #N-grams
            self.unigrams = pd.DataFrame()
            self.bigrams = pd.DataFrame()
            self.trigrams = pd.DataFrame()
            self.fourgrams = pd.DataFrame()
            self.fivegrams = pd.DataFrame()
            self.fill_unigrams()
            self.tab_widget.tabNGram.btBiGram.setEnabled(False)
            self.tab_widget.tabNGram.btTriGram.setEnabled(False)
            self.tab_widget.tabNGram.bt4Gram.setEnabled(False)
            self.tab_widget.tabNGram.bt5Gram.setEnabled(False)
            
            self.just_refresh = False
        else:
            self.msgBox.setText("The data has not been changed")
            self.msgBox.setWindowTitle("KeyText Version 0.16")
            self.msgBox.setStandardButtons(QMessageBox.Ok)
            self.msgBox.show()
            return
            
        

    def openFile(self):

        fnames = QFileDialog.getOpenFileNames(self, "Open CSV Files", "", "CSV and TXT files (*.csv *.txt);;CSV files (*.csv);;TXT files (*.txt)")
               
        if len(fnames[0]) == 0:
            self.msgBox.setText("There is no file to upload!")
            self.msgBox.setWindowTitle("KeyText Version 0.16")
            self.msgBox.setStandardButtons(QMessageBox.Ok)
            self.msgBox.show()
            return
        
        list_of_files = []
        listFileNames = []
        
        file_is_a_csv = True
        
        # Checking all files must be the same type, either csv or txt
        for idx, fn in enumerate(fnames[0]):
            if idx == 0:
                if fn.endswith('.csv'):
                    file_is_a_csv = True
                elif fn.endswith('.txt'):
                    file_is_a_csv = False
                else:
                    return
            else:
                if fn.endswith('.csv'):
                    if not file_is_a_csv:
                        #print('Files must be the same')
                        self.msgBox.setText("All files must be of the same type, csv or txt")
                        self.msgBox.setWindowTitle("KeyText Version 0.16")
                        self.msgBox.setStandardButtons(QMessageBox.Ok)
                        self.msgBox.show()
                        return
                elif fn.endswith('.txt'):
                    if file_is_a_csv:
                        #print('Files must be the same')
                        self.msgBox.setText("All files must be of the same type, csv or txt")
                        self.msgBox.setWindowTitle("KeyText Version 0.16")
                        self.msgBox.setStandardButtons(QMessageBox.Ok)
                        self.msgBox.show()
                        return
                else:
                    self.msgBox.setText("All files must be of the same type, csv or txt")
                    self.msgBox.setWindowTitle("KeyText Version 0.16")
                    self.msgBox.setStandardButtons(QMessageBox.Ok)
                    self.msgBox.show()
                    return
                
            
 
        
        if fnames[0][0].endswith('.csv'):
            for fn in fnames[0]:
                dfcsv = pd.read_csv(open(fn, encoding = 'utf-8', errors = 'backslashreplace'))
                     
                if len(fnames[0])>1:
                    fileName = os.path.basename(fn)[:-4]
                    self.list_of_DataFiles.append(fileName)
                    listData = [fileName]*len(dfcsv)
                    dfcsv.insert(loc=1, column='Data', value=listData)
                    listFileNames.append(fileName)
                
                
                list_of_files.append(dfcsv)
                
                #print('No ' + str(len(listFileNames)))
                #print(listFileNames)
        else:
            default_delimiter = "\\n"
            delimiter, ok = QInputDialog.getText(self, "Paragraph delimiter", "Enter custom paragraph delimiter:", text=default_delimiter)
            delimiter = delimiter.replace('\\n','\n')
            if not ok:
                return
            
            for fn in fnames[0]:
                with open(fn, 'r', encoding='utf-8') as file:
                    paragraphs = file.read().split(delimiter)
                    #text = file.read()
                    
                
                
                pars = [p for p in paragraphs if p]
                #pars = [p.replace('\n',' ') for p in paragraphs if p]
                #print("Pars is "+str(len(pars)))
                if len(fnames[0])>1:
                    fileName = os.path.basename(fn)[:-4]
                    self.list_of_DataFiles.append(fileName)
                    listData = [fileName]*len(pars)
                    #dfcsv.insert(loc=1, column='Data', value=listData)
                    dftext = pd.DataFrame({'Text':pars, 'Data': listData})
                    listFileNames.append(fileName)
                else:
                    dftext = pd.DataFrame({'Text': pars}) 
                
                list_of_files.append(dftext)
                    
                #df = pd.DataFrame({'Paragraphs': paragraphs})
                
            
        
        #print(len(list_of_files))
        
        listFileNames.sort()
        
            
        df = pd.concat(list_of_files, ignore_index=True)
        #df.drop_duplicates(keep=False,inplace=True)
        df.drop_duplicates(inplace=True)
        
        if 'Date' not in df.columns:
            df['Date'] = datetime.now().date()

        
        self.main_data = df
    
            
                       
        
        daftar_kolom = ['Select'] + list(df.columns)
        
        self.tab_widget.tabRawData.cbDate.addItems(daftar_kolom)
        self.tab_widget.tabRawData.cbText.addItems(daftar_kolom)
        
        
        model = pandasModel(df)
        self.tab_widget.tabRawData.tvRawData.setModel(model)
        
        self.actionOpen.setDisabled(True)
        
        
     
    
    def saveData(self):
       
        #idx_tab = self.tab_widget.tabs.currentIndex()
        
        #if idx_tab == 1:
        if not self.main_data_hastobe_saved:
            self.msgBox.setText("The data has not been changed")
            self.msgBox.setWindowTitle("KeyText Version 0.16")
            self.msgBox.setStandardButtons(QMessageBox.Ok)
            self.msgBox.show()
            return
        else:
            filename = QFileDialog.getSaveFileName(self, 'Save File', '', 'CSV data files (*.csv)')
            savename = filename[0]
                   
            if len(savename.strip()) == 0:
                self.msgBox.setText("There is no file to save!")
                self.msgBox.setWindowTitle("KeyText Version 0.16")
                self.msgBox.setStandardButtons(QMessageBox.Ok)
                self.msgBox.show()
                return
            
            self.main_data.to_csv(savename, date_format='%Y.%m.%d', encoding = 'utf-8', index=False)
            self.main_data_hastobe_saved = False
    
        
        
                
                
        #print('Save data and file name ' + savename[0])
  
# Creating tab widgets 
class MyTabWidget(QTabWidget): 
    def __init__(self, parent): 
        #super(QWidget, self).__init__(parent) 
        super(QTabWidget, self).__init__(parent)
        self.parent = parent
        self.layout = QVBoxLayout(self) 
        self.title = 'MyTabWidget'
  
        # Initialize tab screen 
        self.tabs = QTabWidget() 
        self.tabRawData = tabRawData(parent = self)
        
        
        self.tabWordVector = tabWordVector(parent = self)
        
        
        self.tabKata = tabKataDalamKonteks(parent = self)
        self.tabKata.setDisabled(True)
        self.tabKata.setVisible(False)
        
        self.tabComparison = tabCombinedComparison(parent = self)
        self.tabComparison.setDisabled(True)
        self.tabComparison.setVisible(False)
        
        self.tabNGram = tabNGram(parent = self)
        self.tabNGram.setDisabled(True)
        self.tabNGram.setVisible(False)
        
        # Add tabs 
        self.tabs.addTab(self.tabRawData, "Raw Data") 
        self.tabs.addTab(self.tabWordVector, "Search KeyWord")
        self.tabs.addTab(self.tabKata,"KWIC")
        self.tabs.addTab(self.tabComparison,"Category Comparison")
        self.tabs.addTab(self.tabNGram,"N-Gram")
        #self.tabs.addTab(self.tabData,"Data File Comparison")  
        # Add tabs to widget 
        self.layout.addWidget(self.tabs) 
        
        label = QLabel("Copyright ©2025 Ikbal Maulana")

        # Align the label to the bottom-right corner
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)

        self.layout.addWidget(label)
        
        self.setLayout(self.layout) 
        

    
    
        
class tabRawData(QTabWidget):
    def __init__(self, parent): 
        #super(QWidget, self).__init__(parent)
        super(QTabWidget, self).__init__(parent)
        
        self.parent = parent
        
        self.msgBox = QMessageBox()
        
        self.glRawData = QGridLayout()
        
        
        self.lbLang = QLabel()
        self.lbLang.setText('Language')
        self.lbLang.setAlignment(Qt.AlignRight)
        
        self.cbLang = QComboBox()
        self.cbLang.addItems(['Indonesia', 'English'])
        
        
        self.lbDate = QLabel()
        self.lbDate.setText('Date')
        self.lbDate.setAlignment(Qt.AlignRight)
        
        self.rbDayFirst = QRadioButton("Day First")
        
        self.cbDate = QComboBox()
        
        self.lbText = QLabel()
        self.lbText.setText("Text")
        self.lbText.setAlignment(Qt.AlignRight)
        
        self.cbText = QComboBox()
        
        
        
        self.btSelectColumns = QtWidgets.QPushButton()
        
        self.btSelectColumns.setText("Select Text")
        
        self.btSelectColumns.clicked.connect(self.selectColumns)
        
        self.tvRawData = QTableView()
        
        self.glRawData.addWidget(self.lbLang, 0, 0)
        self.glRawData.addWidget(self.cbLang, 0, 1)
        

        self.glRawData.addWidget(self.lbDate, 0, 2)
        self.glRawData.addWidget(self.cbDate, 0, 3)
        self.glRawData.addWidget(self.rbDayFirst, 0, 4)
        
        self.glRawData.addWidget(self.lbText, 0, 5)
        self.glRawData.addWidget(self.cbText, 0, 6)
        self.glRawData.addWidget(self.btSelectColumns, 0, 7)
        self.glRawData.addWidget(self.tvRawData, 1, 0, 6, 8)
        
        
        self.setLayout(self.glRawData)

    
        

    def selectColumns(self):
        def keep_alphanumeric(input_string):
            # Use isalnum() to check if each character is alphanumeric
            alphanumeric_chars = [char if char.isalnum() or char=='_' or char=='-' else ' ' for char in input_string]
            
            # Join the alphanumeric characters to form the resulting string
            result_string = ''.join(alphanumeric_chars)
            
            pattern = r'[a-zA-Z0-9]'
            
            # Search for an alphanumeric character in the string
            if re.search(pattern, result_string):
                return result_string
            else:
                return ""
            
            #return result_string
        
        df = self.parent.parent.main_data
        #print(self.parent.currentWidget())
        #if self.parent.currentWidget() == self.parent.tabRawData:
        if not self.parent.parent.just_refresh:
            print("Masuk tabRawData")
            if self.cbText.currentText() == 'Select':
                self.msgBox.setText("Please select at least one item")
                self.msgBox.setWindowTitle("Warning")
                self.msgBox.setStandardButtons(QMessageBox.Ok)
                self.msgBox.show()
                return
            else: 
                #selected_column = self.cbText.currentText()
                if not self.parent.parent.main_data_hasbeen_changed:
                    print("Has been changed!!!")
                    if self.cbText.currentText() != 'SelectedColumn' :
                        if 'SelectedColumn' in df.columns:
                            df = df.drop('SelectedColumn', axis=1)
                        #df = df.rename(columns={ self.cbText.currentText(): 'SelectedColumn'}  )
                        df['SelectedColumn'] = df[self.cbText.currentText()].str.lower()
                        
                   
                if self.cbDate != 'Select':
                    df = df.rename(columns={ self.cbDate.currentText(): 'Date'})
                    if len(str(df['Date'].iloc[0])) > 4:
                        if self.rbDayFirst.isChecked():
                            dayfirst = True
                        else:
                            dayfirst = False
                            
                        df['Date'] = pd.to_datetime(df['Date'],dayfirst=dayfirst).dt.date
                   
                
                                        
            
        #df = df.dropna(subset=['SelectedColumn']).drop(df[df['SelectedColumn'] == ''].index)
        df['SelectedColumn'] = df['SelectedColumn'].fillna('')
        
        comments = df['SelectedColumn'].to_list()
        
        comments = [s for s in comments if s is not None and (isinstance(s, str) and s.strip() != '')]
        
        comments_for_prev_next_words = comments #it will be broken down into part of sentences
        
        comments = [keep_alphanumeric(s) for s in comments]
        
        token_comments = [s.split() for s in comments]
        
        wv_model = Word2Vec(
            sentences = token_comments,
            min_count = 20,
            vector_size = 200,
            window = 3,
            compute_loss = True,
            sg = 1
        )
        
        
       
        if self.cbDate.currentText() != 'Select':
            df = df.rename(columns={ self.cbDate.currentText(): 'Date'}  )
            self.parent.parent.useDate = True 
            
            if len(str(df['Date'].iloc[0])) > 4:
                if self.rbDayFirst.isChecked():
                    dayfirst = True
                else:
                    dayfirst = False
                    
                df['Date'] = pd.to_datetime(df['Date'],dayfirst=dayfirst).dt.date
                
                

        self.parent.parent.main_data = df
        self.parent.parent.wv_model = wv_model
        
        #Create list of stopwords
        if self.cbLang.currentText() == 'Indonesia':
            
            textfile  = open(os.getcwd()+"/stopwords-id.txt", "r")
            #self.parent.parent.stop_words = textfile.read().split()
            list_stop_words = textfile.read().split()
            self.parent.parent.stop_words = list_stop_words
            
            
            
            
        else:
            textfile  = open(os.getcwd()+"/stopwords-en.txt", "r")
            
            list_stop_words = textfile.read().split()
            self.parent.parent.stop_words = list_stop_words
            
        
        
        # Create Dictionary for next KeyWords
        self.parent.parent.word_freq_dict = defaultdict(list)
        self.parent.parent.prev_word_freq_dict = defaultdict(list)
    
        # Iterate over each text in the 'Text' column
        #for text in df['SelectedColumn']:
        
        
        for text in comments_for_prev_next_words:
            # First, split text into chunks by punctuation (except - and _)
            chunks = re.split(r'[^\w\s\-_]', text.lower())
        
            for chunk in chunks:
                # From each chunk, extract words allowing - or _ in the middle only
                words = re.findall(r'\b\w+(?:[-_]\w+)*\b', chunk)
        
                for i, word in enumerate(words):
                    if i + 1 < len(words):
                        next_word = words[i + 1]
                        self.parent.parent.word_freq_dict[word].append(next_word)
                    if i > 0:
                        prev_word = words[i - 1]
                        self.parent.parent.prev_word_freq_dict[word].append(prev_word)

        
        
        
        self.setEnabled(False)
        #self.parent.tabCleanData.setEnabled(True)
        self.parent.tabs.setCurrentIndex(1)
        self.parent.tabKata.setEnabled(True)
        self.parent.tabComparison.setEnabled(True)
        self.parent.tabNGram.setEnabled(True)
        
        
class tabCombinedComparison(QTabWidget):
    def __init__(self, parent): 
        #super(QWidget, self).__init__(parent)
        super(QTabWidget, self).__init__(parent)
        
        self.parent = parent
        
        self.all_words = ''
        self.df_graph_to_save = pd.DataFrame()
        
        self.msgBox = QMessageBox()
        
        self.glComparison = QGridLayout()
        
        self.lbSearchAllWords1 = QLabel()
        self.lbSearchAllWords1.setText('Keywords')
        self.leSearchAllWords1 = QLineEdit()
        self.leSearchAllWords1.setEnabled(False)
        self.lbAsGroup1 = QLabel('As')
        self.leAsGroup1 = QLineEdit()
        self.leAsGroup1.setEnabled(False)
        self.btAdd1 = QPushButton('+')
        self.btAdd1.setObjectName("bt1")
        self.btAdd1.clicked.connect(self.addAllWords) 
        self.btMinus1 = QPushButton('-')
        self.btMinus1.setObjectName('min1')
        self.btMinus1.clicked.connect(self.clearAllWords)        
        
        self.lbSearchAllWords2 = QLabel()
        self.lbSearchAllWords2.setText('Keywords')
        self.leSearchAllWords2 = QLineEdit()
        self.leSearchAllWords2.setEnabled(False)
        self.lbAsGroup2 = QLabel('As')
        self.leAsGroup2 = QLineEdit()
        self.leAsGroup2.setEnabled(False)
        self.btAdd2 = QPushButton('+')
        self.btAdd2.setObjectName("bt2")
        self.btAdd2.clicked.connect(self.addAllWords) 
        self.btMinus2 = QPushButton('-')
        self.btMinus2.setObjectName('min2')
        self.btMinus2.clicked.connect(self.clearAllWords)
        
        self.lbSearchAllWords3 = QLabel()
        self.lbSearchAllWords3.setText('Keywords')
        self.leSearchAllWords3 = QLineEdit()
        self.leSearchAllWords3.setEnabled(False)
        self.lbAsGroup3 = QLabel('As')
        self.leAsGroup3 = QLineEdit()
        self.leAsGroup3.setEnabled(False)
        self.btAdd3 = QPushButton('+')
        self.btAdd3.setObjectName("bt3")
        self.btAdd3.clicked.connect(self.addAllWords) 
        self.btMinus3 = QPushButton('-')
        self.btMinus3.setObjectName('min3')
        self.btMinus3.clicked.connect(self.clearAllWords)
        
        self.btSidebySideGraph = QPushButton('Side by Side')
        #self.btGraph.setEnabled(False)
        self.btSidebySideGraph.clicked.connect(self.sideBySideComparison)
        
        self.btFilteredComparison = QPushButton('Filtered')
        self.btFilteredComparison.clicked.connect(self.filteredComparison)
        
        self.btSave = QPushButton('Save')
        self.btSave.clicked.connect(self.saveComparison)
        
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setParent(self)
        #self.canvas.setVisible(False)
        self.toolbar = NavigationToolbar(self.canvas, self)
        #self.toolbar.setVisible(False)
        
        self.glComparison.addWidget(self.lbSearchAllWords1, 0, 0)
        #self.glComparison.addWidget(self.leSearchAllWords1, 0, 1, 1, 3)
        self.glComparison.addWidget(self.leSearchAllWords1, 0, 1)
        self.glComparison.addWidget(self.lbAsGroup1, 0, 4)
        self.glComparison.addWidget(self.leAsGroup1, 0, 5)
        self.glComparison.addWidget(self.btAdd1, 0, 6)
        self.glComparison.addWidget(self.btMinus1, 0, 7)
        self.glComparison.addWidget(self.btSidebySideGraph, 0, 8)
        
        self.glComparison.addWidget(self.lbSearchAllWords2, 1, 0)
        #self.glComparison.addWidget(self.leSearchAllWords2, 1, 1, 1, 3)
        self.glComparison.addWidget(self.leSearchAllWords2, 1, 1)
        self.glComparison.addWidget(self.lbAsGroup2, 1, 4)
        self.glComparison.addWidget(self.leAsGroup2, 1, 5)
        self.glComparison.addWidget(self.btAdd2, 1, 6)
        self.glComparison.addWidget(self.btMinus2, 1, 7)
        self.glComparison.addWidget(self.btFilteredComparison, 1, 8)
        
        self.glComparison.addWidget(self.lbSearchAllWords3, 2, 0)
        #self.glComparison.addWidget(self.leSearchAllWords3, 2, 1, 1, 3)
        self.glComparison.addWidget(self.leSearchAllWords3, 2, 1)
        self.glComparison.addWidget(self.lbAsGroup3, 2, 4)
        self.glComparison.addWidget(self.leAsGroup3, 2, 5)
        self.glComparison.addWidget(self.btAdd3, 2, 6)
        self.glComparison.addWidget(self.btMinus3, 2, 7)
        self.glComparison.addWidget(self.btSave, 2, 8)
        
        self.glComparison.addWidget(self.toolbar, 3, 0, 1, 2)
        
        self.glComparison.addWidget(self.canvas, 4, 0, 6, 9)
        
        
        self.setLayout(self.glComparison)
        
    def saveComparison(self):
        if len(self. df_graph_to_save)>0:
            filename = QFileDialog.getSaveFileName(self, 'Save File', '', 'CSV data files (*.csv)')
            savename = filename[0]
            
            if len(savename.strip()) == 0:
                self.msgBox.setText("There is no file to save!")
                self.msgBox.setWindowTitle("KeyText Version 0.16")
                self.msgBox.setStandardButtons(QMessageBox.Ok)
                self.msgBox.show()
                return
            
            self.df_graph_to_save.to_csv(savename)
        
    def sideBySideComparison(self):
        def wholeword(text,keywords):
            pattern = r"\b(?:\w)+"
            words = re.findall(pattern,text.lower())
            return any(keyword in words for keyword in keywords)
        
        df = self.parent.parent.main_data.copy()
        keywords1 = [w.strip() for w in self.leSearchAllWords1.text().split('|') if w.strip() != '']
        keywords2 = [w.strip() for w in self.leSearchAllWords2.text().split('|') if w.strip() != '']
        keywords3 = [w.strip() for w in self.leSearchAllWords3.text().split('|') if w.strip() != '']
        
        if not (keywords1 or keywords2 or keywords3):
            self.msgBox.setText("Please provide keywords to generate the chart")
            self.msgBox.setWindowTitle("KeyText Version 0.16")
            self.msgBox.setStandardButtons(QMessageBox.Ok)
            self.msgBox.show()
            return
        
        all_labels = [] 
        if keywords1:
            label1 = self.leAsGroup1.text().strip()
            if label1 != '':
                df[label1] = df['SelectedColumn'].apply(lambda x: 1 if wholeword(x,keywords1) else 0)
                all_labels.append(label1)
            else:
                df['keywords1'] = df['SelectedColumn'].apply(lambda x: 1 if wholeword(x,keywords1) else 0)
                all_labels.append('keywords1')
                
        if keywords2:
            label2 = self.leAsGroup2.text().strip()
            if label2 != '':
                df[label2] = df['SelectedColumn'].apply(lambda x: 1 if wholeword(x,keywords2) else 0)
                all_labels.append(label2)
            else:
                df['keywords2'] = df['SelectedColumn'].apply(lambda x: 1 if wholeword(x,keywords2) else 0)
                all_labels.append('keywords2')
        if keywords3:
            label3 = self.leAsGroup3.text().strip()
            if label3 != '':
                df[label3] = df['SelectedColumn'].apply(lambda x: 1 if wholeword(x,keywords3) else 0)
                all_labels.append(label3)
            else:
                df['keywords3'] = df['SelectedColumn'].apply(lambda x: 1 if wholeword(x,keywords3) else 0)
                all_labels.append('keywords3')
        
        
        df = df[['Date'] + all_labels]
        df_summed = df.groupby('Date').sum().reset_index()
        
        
        start_date = df_summed['Date'].min()
        end_date = df_summed['Date'].max()
        date_range = pd.date_range(start = start_date, end = end_date)
        
        self.df_graph_to_save = df_summed

        self.figure.clear()
        self.ax = self.figure.add_subplot(111)

        self.ax.set_xlim(start_date, end_date)
        
        # Assuming you have date_range already calculated
        num_dates = len(date_range)
        
        # Calculate the interval n
        n = max(1, num_dates // 10)
        
        for i, label in enumerate(all_labels):
            print(str(i) + ' ' + label)
            self.ax.plot(df_summed.set_index('Date').iloc[:, i], label=label)
            #self.ax.plot(df_summed.iloc[:, i], label=label)
        
        self.ax.xaxis.set_major_locator(mdates.DayLocator(interval = n))
        
        self.ax.set_ylabel('Frequency')
        self.ax.set_xlabel('Date')
        #self.ax.set_title('Keyword Frequencies')
        self.ax.legend()
        
        # dipindah ke terakhir
        self.ax.xaxis.set_tick_params(rotation=30)
        
        self.canvas.draw()
        self.btSave.setEnabled(True)
        print('Selesai chart')
        
    
    def filteredComparison(self):
        def wholeword(text,keywords):
            pattern = r"\b(?:\w)+"
            words = re.findall(pattern,text.lower())
            return any(keyword in words for keyword in keywords)
        
        df = self.parent.parent.main_data.copy()
        keywords1 = [w.strip() for w in self.leSearchAllWords1.text().split('|') if w.strip() != '']
        keywords2 = [w.strip() for w in self.leSearchAllWords2.text().split('|') if w.strip() != '']
        keywords3 = [w.strip() for w in self.leSearchAllWords3.text().split('|') if w.strip() != '']
        
        if not (keywords1 or keywords2 or keywords3):
            self.msgBox.setText("Please provide keywords to generate the chart")
            self.msgBox.setWindowTitle("KeyText Version 0.16")
            self.msgBox.setStandardButtons(QMessageBox.Ok)
            self.msgBox.show()
            return
        
        all_labels = [] 
        
        pattern = '|'.join([f'\\b{word}\\b' for word in keywords1])

        # Filter the dataframe
        #df = df_main[df_main['SelectedColumn'].str.contains(pattern, regex=True, case=False, na=False)]
        
        # keywords1 is the BASE
        if keywords1:
            df['SelectedColumn'] = df['SelectedColumn'].apply(lambda x: x if wholeword(x,keywords1) else 'xxxxxxxxxxxxxxxxxxx')
            #label1 = self.leAsGroup1.text().strip()
            '''
            if label1 != '':
                df[label1] = df['SelectedColumn'].apply(lambda x: 1 if wholeword(x,keywords1) else 0)
                all_labels.append(label1)
            else:
                df['keywords1'] = df['SelectedColumn'].apply(lambda x: 1 if wholeword(x,keywords1) else 0)
                all_labels.append('keywords1')
            '''
        else:
            self.msgBox.setText("Please provide keywords to generate the base data")
            self.msgBox.setWindowTitle("KeyText Version 0.16")
            self.msgBox.setStandardButtons(QMessageBox.Ok)
            self.msgBox.show()
            return
            
        if keywords2:
            label2 = self.leAsGroup2.text().strip()
            if label2 != '':
                df[label2] = df['SelectedColumn'].apply(lambda x: 1 if wholeword(x,keywords2) else 0)
                all_labels.append(label2)
            else:
                df['keywords2'] = df['SelectedColumn'].apply(lambda x: 1 if wholeword(x,keywords2) else 0)
                all_labels.append('keywords2')
        if keywords3:
            label3 = self.leAsGroup3.text().strip()
            if label3 != '':
                df[label3] = df['SelectedColumn'].apply(lambda x: 1 if wholeword(x,keywords3) else 0)
                all_labels.append(label3)
            else:
                df['keywords3'] = df['SelectedColumn'].apply(lambda x: 1 if wholeword(x,keywords3) else 0)
                all_labels.append('keywords3')
        
        print('Cetak df')
        print(df[~df['SelectedColumn'].str.contains('xxxxxxxxxxxxxxxxxxx', regex=False, case=False, na=False)]['SelectedColumn'].head().tolist())
        
        df = df[['Date'] + all_labels]
        df_summed = df.groupby('Date').sum().reset_index()
        
        
        start_date = df_summed['Date'].min()
        end_date = df_summed['Date'].max()
        date_range = pd.date_range(start = start_date, end = end_date)
        
        self.df_graph_to_save = df_summed

        self.figure.clear()
        self.ax = self.figure.add_subplot(111)

        self.ax.set_xlim(start_date, end_date)
        
        # Assuming you have date_range already calculated
        num_dates = len(date_range)
        
        # Calculate the interval n
        n = max(1, num_dates // 10)
        
        for i, label in enumerate(all_labels):
            print(str(i) + ' ' + label)
            self.ax.plot(df_summed.set_index('Date').iloc[:, i], label=label)
            #self.ax.plot(df_summed.iloc[:, i], label=label)
        
        self.ax.xaxis.set_major_locator(mdates.DayLocator(interval = n))
        
        self.ax.set_ylabel('Frequency')
        self.ax.set_xlabel('Date')
        #self.ax.set_title('Keyword Frequencies')
        self.ax.legend()
        
        # dipindah ke terakhir
        self.ax.xaxis.set_tick_params(rotation=30)
        
        self.canvas.draw()
        self.btSave.setEnabled(True)
        print('Selesai chart')
    
    def clearAllWords(self):
        clicked_button = self.sender().objectName()
        if clicked_button ==  'min1':
            self.leSearchAllWords1.setText('')
            self.leAsGroup1.setText('')
        elif clicked_button ==  'min2':
            self.leSearchAllWords2.setText('')
            self.leAsGroup2.setText('')
        elif clicked_button ==  'min3':
            self.leSearchAllWords3.setText('')
            self.leAsGroup3.setText('')
            
        
    def addAllWords(self):
        #print('Masuk addAllWords')
        #print(self.all_words)
        clicked_button = self.sender().objectName()
        #print('Yang diklik adalah ' + clicked_button)
        if clicked_button == 'bt1': 
            if self.leSearchAllWords1.text().strip()== '':
                self.leSearchAllWords1.setText(self.all_words)
            else:
                self.leSearchAllWords1.setText(self.leSearchAllWords1.text().strip()+ '|' + self.all_words)
                
            self.leSearchAllWords1.setEnabled(True)
            self.leAsGroup1.setEnabled(True)
        elif clicked_button == 'bt2':
            if self.leSearchAllWords2.text().strip()== '':
                self.leSearchAllWords2.setText(self.all_words)
            else:
                self.leSearchAllWords2.setText(self.leSearchAllWords2.text().strip()+ '|' + self.all_words)
            
            self.leSearchAllWords2.setEnabled(True)
            self.leAsGroup2.setEnabled(True)
        elif clicked_button == 'bt3':
            if self.leSearchAllWords3.text().strip()== '':
                self.leSearchAllWords3.setText(self.all_words)
            else:
                self.leSearchAllWords3.setText(self.leSearchAllWords3.text().strip()+ '|' + self.all_words)
             
            self.leSearchAllWords3.setEnabled(True)
            self.leAsGroup3.setEnabled(True)
            
        self.all_words = ''
        
        
        
        

class tabWordVector(QTabWidget):
    def __init__(self, parent): 
        #super(QWidget, self).__init__(parent)
        super(QTabWidget, self).__init__(parent)
        
        self.parent = parent
        
        self.df_graph_to_save = pd.DataFrame()
        #self.gml_to_safe = ''
        self.mynetworkgraph = ''
        
        self.msgBox = QMessageBox()
             
        self.glWordVector = QGridLayout()
        
        self.tvWordVector = QTableView()
        self.tvWordVector.setSelectionBehavior(QAbstractItemView.SelectRows)
        # Set selection mode to extended selection (multiple rows)
        self.tvWordVector.setSelectionMode(QAbstractItemView.ExtendedSelection)
        
        
        self.lbSearchKeyWord = QLabel()
        self.lbSearchKeyWord.setText('Keyword')
        self.leSearchKeyWord = QLineEdit()
                
            
        #self.lbSearch = QLabel('Search')
        self.btSearchKeyWord = QPushButton()
        self.btSearchKeyWord.setText('Similar Words')
        self.btSearchKeyWord.clicked.connect(self.searchKeyWordInVectorModel)
        
        self.btNextKeyWord = QPushButton()
        self.btNextKeyWord.setText('Next Words')
        self.btNextKeyWord.clicked.connect(self.nextKeyWords)
        
        self.btPrevKeyWord = QPushButton()
        self.btPrevKeyWord.setText('Previous Words')
        self.btPrevKeyWord.clicked.connect(self.prevKeyWords)
        
        
        
        self.rbIncludeSearchedKeyWord = QRadioButton('Include Searched Keyword')
        
        self.btGraph = QPushButton()
        self.btGraph.setText('Bar Chart')
        self.btGraph.clicked.connect(self.showBarGraph)
        self.btGraph.setEnabled(False)
        
        self.btLineChart = QPushButton() 
        self.btLineChart.setText('Line Chart')
        self.btLineChart.clicked.connect(self.showLineChart)
        self.btLineChart.setEnabled(False)
        '''
        self.btCooccur = QPushButton()
        self.btCooccur.setText('Cooccurence')
        self.btCooccur.clicked.connect(self.showCooccurence)
        self.btCooccur.setEnabled(False)
        '''
        self.btSaveChart = QPushButton()
        self.btSaveChart.setText('Save')
        self.btSaveChart.clicked.connect(self.saveGraph)
        self.btSaveChart.setEnabled(False)
        
        self.btReplaceWords = QPushButton()
        self.btReplaceWords.setText('Replace')
        self.btReplaceWords.clicked.connect(self.replaceWords)
        self.btReplaceWords.setEnabled(True)
        
        self.btCopy = QPushButton()
        self.btCopy.setText('Copy Keywords')
        self.btCopy.clicked.connect(self.copyKeywords)
        self.btCopy.setEnabled(False)
        
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setParent(self)
        self.canvas.setVisible(False)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.setVisible(False)

        self.glWordVector.addWidget(self.lbSearchKeyWord, 0, 0)
        self.glWordVector.addWidget(self.leSearchKeyWord, 0, 1, 1, 2)
        self.glWordVector.addWidget(self.btSearchKeyWord, 0, 3)
        self.glWordVector.addWidget(self.btPrevKeyWord, 0, 4)
        self.glWordVector.addWidget(self.btNextKeyWord, 0, 5)
        self.glWordVector.addWidget(self.btCopy, 0, 6)
        
        self.glWordVector.addWidget(self.rbIncludeSearchedKeyWord, 1, 0, 1, 2)
        self.glWordVector.addWidget(self.btGraph, 1, 2)
        self.glWordVector.addWidget(self.btLineChart, 1, 3)
        #self.glWordVector.addWidget(self.btCooccur, 1, 4)
        self.glWordVector.addWidget(self.btSaveChart, 1, 5)
        self.glWordVector.addWidget(self.btReplaceWords, 1, 6)
        self.glWordVector.addWidget(self.toolbar, 2, 0, 1, 2)
        
                
        self.glWordVector.addWidget(self.tvWordVector, 3, 0, 6, 7)
        self.glWordVector.addWidget(self.canvas, 3, 0, 6, 7)
        
        
        self.setLayout(self.glWordVector)
    
    
    def copyKeywords(self):
        keywords = self.showSelectedValues()
        
        if not keywords:
            keywords = [kw for kw,_ in self.list_of_similar_words]
        
        if self.rbIncludeSearchedKeyWord.isChecked():
            keywords = [self.leSearchKeyWord.text().strip()] + keywords
            
        self.parent.tabComparison.all_words = '|'.join(keywords)
        #self.parent.tabs.setCurrentIndex(3)
        
    
    def replaceWords(self):
        keywords = self.showSelectedValues()
        replacing_word = self.leSearchKeyWord.text().strip()
        
        if not keywords:
            self.msgBox.setText("You have to select one or more words from the table")
            self.msgBox.setWindowTitle("KeyText Version 0.16")
            self.msgBox.setStandardButtons(QMessageBox.Ok)
            self.msgBox.show()
            return
        else:
            # Set the icon, title, and text
            self.msgBox.setIcon(QMessageBox.Question)
            self.msgBox.setWindowTitle("Confirmation")
            self.msgBox.setText("Do you want to replace " + ", ".join(keywords) + " with " + replacing_word + "?")
            
            # Add buttons ("Ok" and "Cancel")
            self.msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            
            # Show the message box and wait for user input
            response = self.msgBox.exec()
            if response != QMessageBox.Ok:
                return
            else:
                df = self.parent.parent.main_data
                # Generate regular expression pattern for whole word matching
                pattern = r'\b(?:{})\b'.format('|'.join(keywords))
                # Replace matching words in the 'Text' column
                #df['SelectedColumn'] = df['SelectedColumn'].str.replace(pattern, replacing_word)         
                df['SelectedColumn'] = df['SelectedColumn'].str.replace(pattern, replacing_word, regex=True)

                #print(pattern)
                #print(replacing_word)
                self.parent.parent.main_data = df
                self.parent.parent.main_data_hasbeen_changed = True
                self.parent.parent.main_data_hastobe_saved = True
        
        
    def showSelectedValues(self):
        selected_values = []
        selected_rows = self.tvWordVector.selectionModel().selectedRows()
        for index in selected_rows:
            
            row_index = index.row()  # Extract row index
            model_index = self.tvWordVector.model().index(row_index, 0)  # Convert row index to QModelIndex
            selected_values.append(self.tvWordVector.model().data(model_index))
        #print("Selected values from first column:", selected_values)
        return selected_values
    
    
    
    def showLineChart(self):
        self.tvWordVector.setVisible(False)
        self.canvas.setVisible(True)
        self.toolbar.setVisible(True)
        
        keywords = self.showSelectedValues()
        
        if not keywords:
            keywords = [kw for kw,_ in self.list_of_similar_words]
        
        if self.rbIncludeSearchedKeyWord.isChecked():
            keywords = [self.leSearchKeyWord.text().strip()] + keywords
              
            
            #print(keywords)
       
        
        df = self.parent.parent.main_data.copy()
        print('Dalam showLineChart')
        #print(df.columns)
        print(self.parent.parent.main_data.columns)
        for kw in keywords:
            df[kw] = df['SelectedColumn'].apply(lambda x: 1 if kw in x.split(' ') else 0)
            
        df_summed = df.groupby('Date').sum().reset_index()
        
        df_summed = df_summed[['Date'] + keywords]
        #print('Banyaknya komen ' + str(len(df_summed)))
        start_date = df['Date'].min()
        end_date = df['Date'].max()
        date_range = pd.date_range(start = start_date, end = end_date)
        
        self.df_graph_to_save = df_summed

        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        
        #for kw in keywords:
        #    self.ax.plot(df_summed['Date'], df_summed[kw], label=kw)
        
        
        self.ax.set_xlim(start_date, end_date)
        #self.ax.plot(df_summed.set_index('Date'))
        #labels = ['Line 1', 'Line 2', 'Line 3']  # Example list of labels
        
        for i, label in enumerate(keywords):
            self.ax.plot(df_summed.set_index('Date').iloc[:, i], label=label)
            #self.ax.plot(df_summed.iloc[:, i], label=label)
        
        # Assuming you have date_range already calculated
        num_dates = len(date_range)
        
        # Calculate the interval n
        n = max(1, num_dates // 10)
        
        #self.ax.gca().xaxis.set_major_locator(mdates.MonthLocator()) 
        #self.ax.xaxis.set_major_locator(mdates.DayLocator(interval = 10))
        self.ax.xaxis.set_major_locator(mdates.DayLocator(interval = n))
        #self.ax.xticks(rotation=30)
        
        self.ax.set_ylabel('Frequency')
        self.ax.set_xlabel('Date')
        #self.ax.set_title('Keyword Frequencies')
        self.ax.legend()
        
        # dipindah ke terakhir
        self.ax.xaxis.set_tick_params(rotation=30)
    
        # Create a canvas for the Matplotlib figure
        self.canvas.draw()
        self.btSaveChart.setEnabled(True)
        #print(df.columns)
        print(self.parent.parent.main_data.columns)
    
    
        
    def showBarGraph(self):
        self.tvWordVector.setVisible(False)
        self.canvas.setVisible(True)
        self.toolbar.setVisible(True)
        
        keywords = self.showSelectedValues()
        
        if not keywords:
            keywords = [kw for kw,_ in self.list_of_similar_words]
        
        if self.rbIncludeSearchedKeyWord.isChecked():
            keywords = [self.leSearchKeyWord.text().strip()] + keywords
              
            
        
        df = self.parent.parent.main_data
        #self.list_keyword_frequency = []
        #keywords = []
        frequencies = []
        for keyword in keywords:
            
            pattern = r'\b{}\b'.format(re.escape(keyword))
            # Count the number of rows containing the keyword as a whole word in the "SelectedColumn"
            count = df['SelectedColumn'].str.contains(pattern, case=False, na=False).sum()
            
            
            #keywords.append(KeyWord)
            #frequency = (df['SelectedColumn'].str.contains(keyword) == True).sum()
            # Append the tuple (keyword, frequency) to the result list
            frequencies.append(count)
            
        self.df_graph_to_save = pd.DataFrame(list(zip(keywords, frequencies)), columns=['Keyword', 'Frequency'])
        
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
    
        self.ax.bar(keywords, frequencies, color='skyblue')
        self.ax.set_xlabel('Keywords')
        self.ax.set_ylabel('Frequency')
        
        # Rotate x-axis labels by 30 degrees
        self.ax.tick_params(axis='x', rotation=30)
        #self.ax.set_title('Keyword Frequencies')
        
        #plt.xticks(ticks=range(0, len(df_results), max(1, len(df_results)//10)), labels=df_results.index.strftime('%Y-%m-%d')[::max(1, len(df_results)//10)], rotation=45)

        
        #self.ax.set_xticklabels(keywords, rotation=30)
        
        
        #df.reindex(df['Date'].unique())
        #self.ax.set_xticklabels(keywords, ticks=range(0, len(df), max(1, len(df)//10)), labels=df.index.strftime('%Y-%m-%d')[::max(1, len(df_results)//10)], rotation=45)

        
    
        # Create a canvas for the Matplotlib figure
        self.canvas.draw()
        #self.canvas = FigureCanvas(self.figure)
        self.btGraph.setEnabled(False)
        #self.btSaveChart.setEnabled(False)
        self.btSaveChart.setEnabled(True)
        
       
    def saveGraph(self):
        if len(self.df_graph_to_save)>0:
            filename = QFileDialog.getSaveFileName(self, 'Save File', '', 'CSV data files (*.csv)')
            savename = filename[0]
            
            if len(savename.strip()) == 0:
                self.msgBox.setText("There is no file to save!")
                self.msgBox.setWindowTitle("KeyText Version 0.16")
                self.msgBox.setStandardButtons(QMessageBox.Ok)
                self.msgBox.show()
                return
            
            self.df_graph_to_save.to_csv(savename)
        else:
            filetypes = "GML (*.gml);;GRAPHML (*.graphml)"
            #filename = QFileDialog.getSaveFileName(self, 'Save File', '', 'graph files (*.graphml)')
            filename = QFileDialog.getSaveFileName(self, 'Save File', '', filetypes)
            savename = filename[0]
                   
            if len(savename.strip()) == 0:
                self.msgBox.setText("There is no file to save!")
                self.msgBox.setWindowTitle("TopMod Version 0.42")
                self.msgBox.setStandardButtons(QMessageBox.Ok)
                self.msgBox.show()
                return
            
            nx.write_gml(self.mynetworkgraph, savename)
            
        self.btSaveChart.setEnabled(False)

    
    def listPrevNextKeyWords(self, word, mydictionary):
        probable_words = mydictionary[word]
        word_counts = pd.Series(probable_words).value_counts(normalize=True).reset_index()
        word_counts.columns = ['word', 'Probability']
        # Sort the DataFrame by probability in descending order
        word_counts = word_counts.sort_values(by='Probability', ascending=False)
        # Select the top ten most probable words
        top_ten_words_df = word_counts.head(10)
        return top_ten_words_df['word'].tolist()
        
        
        

    def prevKeyWords(self):
        self.tvWordVector.setVisible(False)
        self.canvas.setVisible(False)
        self.toolbar.setVisible(False)
        
        word_to_check = self.leSearchKeyWord.text().strip()
        if word_to_check not in self.parent.parent.prev_word_freq_dict:
            self.msgBox.setText("The keyword is not in the text")
            self.msgBox.setWindowTitle("KeyText Version 0.16")
            self.msgBox.setStandardButtons(QMessageBox.Ok)
            self.msgBox.show()
            return
        if self.parent.parent.unigrams.empty:
            self.msgBox.setText("The data of unigrams will be created")
            self.msgBox.setWindowTitle("KeyText Version 0.16")
            self.msgBox.setStandardButtons(QMessageBox.Ok)
            self.msgBox.show()
            self.parent.parent.fill_unigrams()
        
        probable_words = self.parent.parent.prev_word_freq_dict[word_to_check]
        print(probable_words)
        
        # Count the frequency of each probable word
        word_counts = pd.Series(probable_words).value_counts().reset_index()
        print(word_counts)
        
        word_counts.columns = ['Word', 'Frequency']
        unigrams = self.parent.parent.unigrams
        
        print(unigrams.head())
        
        freq = unigrams.loc[unigrams['Unigram'] == word_to_check, 'Frequency']
        
        # Convert to scalar (int or float)
        freq = freq.iloc[0] if not freq.empty else 0
        
        print('Frequency of ' + word_to_check + " is " + str(freq))
        
        word_counts['logDice'] = 14 + np.log2( 2 * word_counts['Frequency'] / ( \
            word_counts['Word'].map(dict(unigrams.values))  + freq))
            

        word_counts = word_counts.sort_values(by='logDice', ascending=False)
        
        # Select the top ten most probable words
        top_ten_words_df = word_counts.head(10)
        
        model = pandasModel(top_ten_words_df)
        
        #self.list_of_similar_words = [(row['word'], row['Probability']) for _, row in top_ten_words_df.iterrows()]

        self.tvWordVector.setModel(model)
        self.btGraph.setEnabled(True)
        self.btLineChart.setEnabled(True)
        #self.btCooccur.setEnabled(True)
        self.tvWordVector.setVisible(True)
        self.btSaveChart.setEnabled(False)
            
    
    def nextKeyWords(self):
        self.tvWordVector.setVisible(False)
        self.canvas.setVisible(False)
        self.toolbar.setVisible(False)
        
        word_to_check = self.leSearchKeyWord.text().strip()
        if word_to_check not in self.parent.parent.word_freq_dict:
            self.msgBox.setText("The keyword is not in the text")
            self.msgBox.setWindowTitle("KeyText Version 0.16")
            self.msgBox.setStandardButtons(QMessageBox.Ok)
            self.msgBox.show()
            return
        if self.parent.parent.unigrams.empty:
            self.msgBox.setText("The data of unigrams will be created")
            self.msgBox.setWindowTitle("KeyText Version 0.16")
            self.msgBox.setStandardButtons(QMessageBox.Ok)
            self.msgBox.show()
            self.parent.parent.fill_unigrams()
        
        probable_words = self.parent.parent.word_freq_dict[word_to_check]
        # Count the frequency of each probable word
        print(probable_words)
                               
        word_counts = pd.Series(probable_words).value_counts().reset_index()
        print(word_counts)
        
        word_counts.columns = ['Word', 'Frequency']
        
        unigrams = self.parent.parent.unigrams
        
        print(unigrams.head())
        
        freq = unigrams.loc[unigrams['Unigram'] == word_to_check, 'Frequency']

        # Convert to scalar (int or float)
        freq = freq.iloc[0] if not freq.empty else 0

        
        word_counts['logDice'] = 14 + np.log2( 2 * word_counts['Frequency'] / ( freq + \
            word_counts['Word'].map(dict(unigrams.values)) ))
            

        word_counts = word_counts.sort_values(by='logDice', ascending=False)
    
        # Step 7: Select top 10
        #top_ten_bigrams = bigram_counts[['next_word', 'bigram_freq', 'logDice']].head(10).reset_index(drop=True)
        #top_ten_bigrams.columns = ['word', 'Frequency', 'LogDice']

        #word_counts = word_counts.sort_values(by='Probability', ascending=False)
        # Select the top ten most probable words
        top_ten_words_df = word_counts.head(10)
        
        model = pandasModel(top_ten_words_df)
        
        #self.list_of_similar_words = [(row['word'], row['Probability']) for _, row in top_ten_words_df.iterrows()]

        self.tvWordVector.setModel(model)
        self.btGraph.setEnabled(True)
        self.btLineChart.setEnabled(True)
        #self.btCooccur.setEnabled(True)
        self.tvWordVector.setVisible(True)
        self.btSaveChart.setEnabled(False)
            
    
    def searchKeyWordInVectorModel(self):
        self.tvWordVector.setVisible(False)
        self.canvas.setVisible(False)
        self.toolbar.setVisible(False)
        
        word_to_check = self.leSearchKeyWord.text().strip()
        if word_to_check not in self.parent.parent.wv_model.wv.key_to_index:
            self.msgBox.setText("The keyword is not in the text")
            self.msgBox.setWindowTitle("KeyText Version 0.16")
            self.msgBox.setStandardButtons(QMessageBox.Ok)
            self.msgBox.show()
            return
        else:
            self.list_of_similar_words = self.parent.parent.wv_model.wv.most_similar(word_to_check)
            df = pd.DataFrame(self.list_of_similar_words, columns=['Keyword', 'Weight'])
            model = pandasModel(df)
            
            #if self.rbIncludeSearchedKeyWord.isChecked():
            #    self.list_of_similar_words = [(word_to_check,1)] + self.list_of_similar_words
                
            self.tvWordVector.setModel(model)
            self.btGraph.setEnabled(True)
            self.btLineChart.setEnabled(True)
            #self.btCooccur.setEnabled(True)
            self.tvWordVector.setVisible(True)
            self.btSaveChart.setEnabled(False)
            self.btCopy.setEnabled(True)



class tabNGram(QTabWidget):
    def __init__(self, parent): 
        #super(QWidget, self).__init__(parent) 
        super(QTabWidget, self).__init__(parent)
        
        self.parent = parent
        
        # Create a scrollable area for the canvas
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        self.data_representation = ""
        self.glayout = QGridLayout()
        
        self.btUniGram = QPushButton()
        self.btUniGram.setText("UniGram")
        self.btUniGram.clicked.connect(self.createUniGram)
        self.btUniGram.setEnabled(True)
        
        self.btBiGram = QPushButton()
        self.btBiGram.setText("BiGram")
        self.btBiGram.clicked.connect(self.createBiGram)
        self.btBiGram.setEnabled(False)
        
        self.btTriGram = QPushButton()
        self.btTriGram.setText("TriGram")
        self.btTriGram.clicked.connect(self.createTriGram)
        self.btTriGram.setEnabled(False)
        
        self.bt4Gram = QPushButton()
        self.bt4Gram.setText("Four-Gram")
        self.bt4Gram.clicked.connect(self.create4Gram)
        self.bt4Gram.setEnabled(False)
        
        self.bt5Gram = QPushButton()
        self.bt5Gram.setText("Five-Gram")
        self.bt5Gram.clicked.connect(self.create5Gram)
        self.bt5Gram.setEnabled(False)
        
        self.rbExcludeStopWords = QRadioButton("Exclude Stop Words")
        
        self.lbMinimumFrequency = QLabel('Minimum Frequency')
        self.sbMinimumFrequency = QSpinBox()
        self.sbMinimumFrequency.setRange(1, 25)       # Set the allowed range
        self.sbMinimumFrequency.setValue(5)          # Set the default value

        #self.sbMinimumFrequency.valueChanged.connect(self.changeMinimumFrequency)
        
        self.lbMinimumLogDice = QLabel('Minimum logDice')
        self.sbMinimumLogDice = QSpinBox()
        self.sbMinimumLogDice.setRange(1, 25)       # Set the allowed range
        self.sbMinimumLogDice.setValue(5)          # Set the default value

        self.cbSortCol = QComboBox()
        self.cbSortCol.addItems([
            "Sort by NGram",
            "Sort by Frequency",
            "Sort by Sum of Unigram Frequencies",
            "Sort by logDice"
        ])
        #self.cbSortCol.setCurrentText("Sort by logDice")
        #self.cbSortCol.currentTextChanged.connect(self.sortColumn)
        
        
        self.btSaveData = QPushButton()
        self.btSaveData.setText("Save")
        self.btSaveData.clicked.connect(self.saveData)
        self.btSaveData.setEnabled(False)
        
        self.tblKataData = QTableView()
        self.tblKataData.setSortingEnabled(True)
        
        self.container = QWidget()
        self.scroll_layout = QVBoxLayout(self.container)
        self.scroll_layout.addWidget(self.tblKataData)
        self.container.setLayout(self.scroll_layout)


        
        # Add the scroll area to the grid layout
        self.glayout.addWidget(self.scroll_area, 3, 0, 7, 12)
        #Batas Tambahan
        
        self.glayout.addWidget(self.btUniGram, 0, 0)
        self.glayout.addWidget(self.btBiGram, 0, 1)
        self.glayout.addWidget(self.btTriGram, 0, 2)
        self.glayout.addWidget(self.bt4Gram, 0, 3)
        self.glayout.addWidget(self.bt5Gram, 0, 4)
        self.glayout.addWidget(self.rbExcludeStopWords, 1, 0)
        self.glayout.addWidget(self.lbMinimumFrequency, 1, 1)
        self.glayout.addWidget(self.sbMinimumFrequency, 1, 2)
        self.glayout.addWidget(self.lbMinimumLogDice, 1, 3)
        #self.glayout.addWidget(self.cbSortCol, 1, 4)
        self.glayout.addWidget(self.sbMinimumLogDice, 1, 4)
        self.glayout.addWidget(self.btSaveData, 1, 5)
        self.glayout.addWidget(self.tblKataData, 3, 0, 5, 12)
        #self.glayout.addWidget(self.canvas, 3, 0, 7, 12)
        
        #self.setLayout(self.glayout)
        
        self.glayout.setRowStretch(4, 5)
        self.glayout.setColumnStretch(4,3)
 
        self.setLayout(self.glayout)
        
        
    def saveData(self):
        # Get model from table
        model = self.tblKataData.model()
    
        # If model is a proxy, get source model
        source_model = model.sourceModel() if hasattr(model, 'sourceModel') else model
    
        if not hasattr(source_model, '_data'):
            QMessageBox.warning(self, "Warning", "No data to save.")
            return
    
        df = source_model._data
    
        # Ask user for file path
        options = QFileDialog.Options()
        filepath, _ = QFileDialog.getSaveFileName(self, "Save Table Data", "", "CSV Files (*.csv);;Excel Files (*.xlsx)", options=options)
    
        if filepath:
            try:
                if filepath.endswith(".csv"):
                    df.to_csv(filepath, index=False)
                elif filepath.endswith(".xlsx"):
                    df.to_excel(filepath, index=False)
                else:
                    # Default to CSV if no extension
                    df.to_csv(filepath + ".csv", index=False)
    
                QMessageBox.information(self, "Success", f"Data saved to:\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file:\n{str(e)}")

        
        
    def sortColumn(self, sort_option):
        sort_column_map = {
            "Sort by NGram": ("NGram", Qt.AscendingOrder),
            "Sort by Frequency": ("Frequency", Qt.DescendingOrder),
            "Sort by Sum of Unigram Frequencies": ("Sum of Unigram Frequencies", Qt.DescendingOrder),
            "Sort by logDice": ("logDice", Qt.DescendingOrder),
        }
    
        column_name, order = sort_column_map[sort_option]
    
        # Make sure to get the proxy model
        proxy_model = self.tblKataData.model()
        source_model = proxy_model.sourceModel() if hasattr(proxy_model, 'sourceModel') else proxy_model
        
        print(source_model._df.columns)
        if hasattr(source_model, '_df'):
            df_columns = list(source_model._df.columns)
            print(df_columns)
            if column_name in df_columns:
                print('Masuk seleksi')
                column_index = df_columns.index(column_name)
                self.tblKataData.sortByColumn(column_index, order)
            elif column_name == 'NGram' and self.data_representation == 'unigram':
                print('Ini unigram')
                column_index = df_columns.index('Unigram')
                self.tblKataData.sortByColumn(column_index, order)
                
                  
        
        
    def createUniGram(self):
        if self.parent.parent.unigrams.empty:
            self.parent.parent.fill_unigrams()
            
        min_freq = self.sbMinimumFrequency.value()

        # Filtering
        filtered_unigrams = self.parent.parent.unigrams[self.parent.parent.unigrams['Frequency'] >= min_freq]
        
        stopwords = self.parent.parent.stop_words
        if self.rbExcludeStopWords.isChecked():
            filtered_unigrams = filtered_unigrams[~filtered_unigrams['Unigram'].isin(stopwords)]
                
        model = pandasModelKWIC(filtered_unigrams)
        self.tblKataData.setModel(model)
        self.tblKataData.resizeColumnToContents(1)
        self.tblKataData.setColumnWidth(1, 400)
        self.tblKataData.setColumnWidth(3, 400)
        
        # Update UI
        #self.lbJumlahCuitan.setText('Number of Texts = ' + str(len(self.df_hasil)))
        #self.btReplaceKWIC.setEnabled(True)
        self.tblKataData.setVisible(True)
        self.btBiGram.setEnabled(True)
        self.btSaveData.setEnabled(True)
        
        self.data_representation = "unigram"   
            
    
    def createNGram(self, N):
        df = self.parent.parent.main_data
        comments = df['SelectedColumn'].dropna().to_list()
        unigram_freq = dict(zip(self.parent.parent.unigrams['Unigram'], self.parent.parent.unigrams['Frequency']))
        #stopwords = set(self.parent.parent.stopwords)  # Make sure this exists
    
        ngram_counts = defaultdict(int)
    
        for text in comments:
            # Split into chunks by punctuation except - and _
            chunks = re.split(r'[^\w\s\-_]', text.lower())
            for chunk in chunks:
                # Extract words allowing - or _ in the middle only
                words = re.findall(r'\b\w+(?:[-_]\w+)*\b', chunk)
                for i in range(len(words) - N + 1):
                    ngram_tokens = words[i:i + N]
                    # Skip N-grams that start or end with stopwords
                    #if ngram_tokens[0] in stopwords or ngram_tokens[-1] in stopwords:
                    #    continue
                    ngram = ' '.join(ngram_tokens)
                    ngram_counts[ngram] += 1
    
        data = []
        for ngram, freq in ngram_counts.items():
            tokens = ngram.split()
            # Calculate logDice if N > 1
            if N == 1:
                logdice = None
            else:
                parts = [unigram_freq.get(t, 1) for t in tokens]  # avoid zero
                #print(f"parts = {parts}, denom = {sum(parts)}, freq = {freq}")
                try:
                    denom = sum(parts)
                    logdice = 14 + np.log2(N * freq /denom)
                    #print("denom =" + str(denom)+ " logDice "+str(logdice))
                except:
                    
                    logdice = 0
            data.append((ngram, freq, denom, logdice))
            
            #It will be sort by logDice in the calling functions
            self.cbSortCol.setCurrentText("Sort by logDice")
    
        return pd.DataFrame(data, columns=['NGram', 'Frequency', 'Sum of Unigram Frequencies', 'logDice'])

    
    
    def createBiGram(self):       
        if self.parent.parent.bigrams.empty:
            self.parent.parent.bigrams = self.createNGram(2)

        df = self.parent.parent.bigrams
            
        min_freq = self.sbMinimumFrequency.value()

        # Filtering
        filtered_bigrams = df[df['Frequency'] >= min_freq].sort_values(by='logDice', ascending=False)
        
        stopwords = self.parent.parent.stop_words
        if self.rbExcludeStopWords.isChecked():
            filtered_bigrams = filtered_bigrams[~filtered_bigrams['NGram'].apply(lambda x: x.split()[0] in stopwords or x.split()[-1] in stopwords)]

        model = pandasModelKWIC(filtered_bigrams)
        self.tblKataData.setModel(model)
        self.tblKataData.resizeColumnToContents(1)
        self.tblKataData.setColumnWidth(1, 400)
        self.tblKataData.setColumnWidth(3, 400)
        
        
        self.tblKataData.setVisible(True)
        self.btTriGram.setEnabled(True)
        
        self.data_representation = "bigram"    
    
    def createTriGram(self):
        if self.parent.parent.trigrams.empty:
            self.parent.parent.trigrams = self.createNGram(3)
        
        df = self.parent.parent.trigrams
        
        min_freq = self.sbMinimumFrequency.value()

        # Filtering
        filtered_trigrams = df[df['Frequency'] >= min_freq].sort_values(by='logDice', ascending=False)
        stopwords = self.parent.parent.stop_words
        if self.rbExcludeStopWords.isChecked():
            filtered_trigrams = filtered_trigrams[~filtered_trigrams['NGram'].apply(lambda x: x.split()[0] in stopwords or x.split()[-1] in stopwords)]
    
        model = pandasModelKWIC(filtered_trigrams)
        self.tblKataData.setModel(model)
        self.tblKataData.resizeColumnToContents(1)
        self.tblKataData.setColumnWidth(1, 400)
        self.tblKataData.setColumnWidth(3, 400)
        
        
        self.tblKataData.setVisible(True)
        self.bt4Gram.setEnabled(True)
        
        self.data_representation = "trigram"    
            
    
    def create4Gram(self):
        if self.parent.parent.fourgrams.empty:
            self.parent.parent.fourgrams = self.createNGram(4)
 
        df = self.parent.parent.fourgrams

        min_freq = self.sbMinimumFrequency.value()

        # Filtering
        filtered_fourgrams = df[df['Frequency'] >= min_freq].sort_values(by='logDice', ascending=False)
        stopwords = self.parent.parent.stop_words
        if self.rbExcludeStopWords.isChecked():
            filtered_fourgrams = filtered_fourgrams[~filtered_fourgrams['NGram'].apply(lambda x: x.split()[0] in stopwords or x.split()[-1] in stopwords)]
        
        
        model = pandasModelKWIC(filtered_fourgrams)
        self.tblKataData.setModel(model)
        self.tblKataData.resizeColumnToContents(1)
        self.tblKataData.setColumnWidth(1, 400)
        self.tblKataData.setColumnWidth(3, 400)
        
        
        self.bt5Gram.setEnabled(True)
        self.tblKataData.setVisible(True)
        
        self.data_representation = "fourgram"  

 
    def create5Gram(self):
        if self.parent.parent.fivegrams.empty:
            self.parent.parent.fivegrams = self.createNGram(5)
 
        df = self.parent.parent.fivegrams

        min_freq = self.sbMinimumFrequency.value()

        # Filtering
        filtered_fivegrams = df[df['Frequency'] >= min_freq].sort_values(by='logDice', ascending=False)
        stopwords = self.parent.parent.stop_words
        if self.rbExcludeStopWords.isChecked():
            filtered_fivegrams = filtered_fivegrams[~filtered_fivegrams['NGram'].apply(lambda x: x.split()[0] in stopwords or x.split()[-1] in stopwords)]
        
        
        model = pandasModelKWIC(filtered_fivegrams)
        self.tblKataData.setModel(model)
        self.tblKataData.resizeColumnToContents(1)
        self.tblKataData.setColumnWidth(1, 400)
        self.tblKataData.setColumnWidth(3, 400)
        
        
        self.tblKataData.setVisible(True)
        
        self.data_representation = "fivegram"  




class tabKataDalamKonteks(QTabWidget):
    def __init__(self, parent): 
        #super(QWidget, self).__init__(parent) 
        super(QTabWidget, self).__init__(parent)
        
        self.parent = parent
        
        self.mynetworkgraph = ""
        
        self.data_representation = ""
        
        self.df_hasil = pd.DataFrame()
        self.data_wordcloud = pd.DataFrame()
        self.windowSpan = 7
        #Ada di baris pertama
        self.glayout = QGridLayout()
        
        self.msgBox = QMessageBox()
        self.msgTextBox = QDialog()
        
        #self.btVisual = QPushButton('Visualization')
        #self.btVisual.clicked.connect(self.visualizingData)
        
        self.lbCariKata = QLabel()
        self.lbCariKata.setText('Words')
        self.leCariKata = QLineEdit()
                
        self.lbCariKiri = QLabel('Left Words')
        #self.lbCariKiri.setVisible(False)
        self.leKataKiri = QLineEdit()
        #self.leKataKiri.setVisible(False)
        
        #self.rbAndLeftRight = QRadioButton("And")
        self.rbAndLeftRight = QCheckBox("And")
        
        self.lbCariKanan = QLabel('Right Words')
        #self.lbCariKanan.setVisible(False)
        self.leKataKanan = QLineEdit()
        #self.leKataKanan.setVisible(False)
        
        self.btSalinKataKata = QPushButton()
        self.btSalinKataKata.setText("Paste Words")
        self.btSalinKataKata.clicked.connect(self.salinKataKata)
    
        #self.lbSearch = QLabel('Search in')
        self.btCariKata = QPushButton()
        self.btCariKata.setText('Search')
        self.btCariKata.clicked.connect(self.cariKataDiData)
        
        #self.cbSelectedColumn = QComboBox()       
        
        
        self.lbJumlahCuitan = QLabel()
        self.lbJumlahCuitan.setAlignment(Qt.AlignCenter)
        
        self.lbWindowSpan = QLabel('Window Span')
        self.sbWindowSpan = QSpinBox()
        self.sbWindowSpan.setRange(1, 25)       # Set the allowed range
        self.sbWindowSpan.setValue(10)          # Set the default value

        self.sbWindowSpan.valueChanged.connect(self.changedWindowSpan)
        
        self.rbExcludeSearchWords = QRadioButton("Exclude Search Words")
        
        self.rbExcludeStopWords = QRadioButton("Exclude Stop Words")
        
        self.btWordCloud = QPushButton()
        self.btWordCloud.setText("Word Cloud")
        self.btWordCloud.clicked.connect(self.createWordCloud)
        
        self.btWordCooccurence = QPushButton()
        self.btWordCooccurence.setText("Cooccurence")
        self.btWordCooccurence.clicked.connect(self.WordCooccurence)
        
        self.btReplaceKWIC = QPushButton()
        self.btReplaceKWIC.setText("Replace Keywords")
        self.btReplaceKWIC.clicked.connect(self.replaceKWIC)
        self.btReplaceKWIC.setEnabled(False)
        
        self.btSaveData = QPushButton()
        self.btSaveData.setText("Save")
        self.btSaveData.clicked.connect(self.saveData)
        self.btSaveData.setVisible(False)
        
        self.tblKataData = QTableView()
        self.tblKataData.setSortingEnabled(True)
        
        # Create figure and canvas
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        
        # Create toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # Create container that includes toolbar + canvas
        self.plot_container = QWidget()
        plot_layout = QVBoxLayout(self.plot_container)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.setSpacing(0)
        plot_layout.addWidget(self.toolbar)   # Toolbar on top
        plot_layout.addWidget(self.canvas)    # Canvas below
        
        # Put plot_container inside a scrollable area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.plot_container)
        
        # Initially hidden
        self.scroll_area.setVisible(False)
        
        # Add scroll area to grid layout
        #self.glayout.addWidget(self.scroll_area, 3, 0, 7, 12)

        
        
        #Tambahan
        # Create a scrollable area for the canvas
        #self.scroll_area = QScrollArea()
        #self.scroll_area.setWidgetResizable(True)
        
        # Create a container widget to hold the canvas
        #self.container = QWidget()
        #self.layout = QVBoxLayout(self.container)
        #self.layout.addWidget(self.canvas)
        
        # Set the container as the scroll area's widget
        #self.scroll_area.setWidget(self.container)
        
        # Add the scroll area to the grid layout
        self.glayout.addWidget(self.scroll_area, 3, 0, 7, 12)
        #Batas Tambahan
        
        self.glayout.addWidget(self.lbCariKata, 0, 0)
        self.glayout.addWidget(self.leCariKata, 0, 1)
        self.glayout.addWidget(self.lbCariKiri, 0, 2)
        self.glayout.addWidget(self.leKataKiri, 0, 3)
        self.glayout.addWidget(self.rbAndLeftRight, 0, 4)
        self.glayout.addWidget(self.lbCariKanan, 0, 5)
        self.glayout.addWidget(self.leKataKanan, 0, 6)
        
        #self.glayout.addWidget(self.lbSearch, 0, 6)
        self.glayout.addWidget(self.btSalinKataKata, 0, 7)
        self.glayout.addWidget(self.btCariKata, 0, 8)
        #self.glayout.addWidget(self.cbSelectedColumn, 0, 7)
        
        self.glayout.addWidget(self.lbWindowSpan, 1, 0)
        self.glayout.addWidget(self.sbWindowSpan, 1, 1)
        self.glayout.addWidget(self.lbJumlahCuitan, 1, 2, 1, 3)
        self.glayout.addWidget(self.rbExcludeSearchWords, 1, 5)
        self.glayout.addWidget(self.btSaveData, 1, 6)
        self.glayout.addWidget(self.btReplaceKWIC, 1, 7)
        
        #self.glayout.addWidget(self.toolbar, 2, 0, 1, 5)
        self.glayout.addWidget(self.rbExcludeStopWords, 2, 3)
        self.glayout.addWidget(self.btWordCloud, 2, 5)
        self.glayout.addWidget(self.btWordCooccurence, 2, 6)
        
        #CLUSTER and DENDORGRAM is turned off
        #self.glayout.addWidget(self.btWordCluster, 2, 7)
        #self.glayout.addWidget(self.btWordDendrogram, 2, 8)
        
        
        
        self.glayout.addWidget(self.tblKataData, 3, 0, 7, 12)
        #self.glayout.addWidget(self.canvas, 3, 0, 7, 12)
        
        #self.setLayout(self.glayout)
        
        self.glayout.setRowStretch(4, 5)
        self.glayout.setColumnStretch(4,3)
 
        self.setLayout(self.glayout)
        
    def saveData(self):
        if self.data_representation == "kwic": 
            filename = QFileDialog.getSaveFileName(self, 'Save File', '', 'CSV data files (*.csv)')
            savename = filename[0]
                   
            if len(savename.strip()) == 0:
                self.msgBox.setText("There is no file to save!")
                self.msgBox.setWindowTitle("KeyText Version 0.16")
                self.msgBox.setStandardButtons(QMessageBox.Ok)
                self.msgBox.show()
                return
            df_to_save = self.df_hasil[['Date','Left','Keywords','Right','SelectedColumn']].sort_values(by='Date').copy()
            #df_to_save = self.df_hasil.sort_values(by='Date').copy()
            df_to_save.rename(columns={'Left': 'Left Words'+ ' = ' + self.leKataKiri.text(), 'Right': 'Right Words' + ' = ' + self.leKataKanan.text()}, inplace=True)
            df_to_save.to_csv(savename, encoding = 'utf-8', index=False)
            
        
            
        elif self.data_representation == "wordcloud":
            filename = QFileDialog.getSaveFileName(self, 'Save File', '', 'CSV data files (*.csv)')
            savename = filename[0]
                   
            if len(savename.strip()) == 0:
                self.msgBox.setText("There is no file to save!")
                self.msgBox.setWindowTitle("KeyText Version 0.16")
                self.msgBox.setStandardButtons(QMessageBox.Ok)
                self.msgBox.show()
                return
            
            

            self.data_wordcloud.to_csv(savename, encoding = 'utf-8', index=False)
           
            
        elif self.data_representation == "cooccurence":
            filename = QFileDialog.getSaveFileName(self, 'Save File', '', 'CSV data files (*.csv)')
            savename = filename[0]
                   
            if len(savename.strip()) == 0:
                self.msgBox.setText("There is no file to save!")
                self.msgBox.setWindowTitle("KeyText Version 0.16")
                self.msgBox.setStandardButtons(QMessageBox.Ok)
                self.msgBox.show()
                return
            df_to_save = self.df_cooccurence.copy()
            #df_to_save = self.df_hasil.sort_values(by='Date').copy()
            #df_to_save.rename(columns={'Left': 'Left Words'+ ' = ' + self.leKataKiri.text(), 'Right': 'Right Words' + ' = ' + self.leKataKanan.text()}, inplace=True)
            df_to_save.to_csv(savename, encoding = 'utf-8', index=False)
            
        elif self.data_representation == "dendrogram":
            filename = QFileDialog.getSaveFileName(self, 'Save File', '', 'text file (*.txt)')
            savename = filename[0]
            
            if len(savename.strip()) == 0:
                self.msgBox.setText("There is no file to save!")
                self.msgBox.setWindowTitle("KeyText Version 0.16")
                self.msgBox.setStandardButtons(QMessageBox.Ok)
                self.msgBox.show()
                return
   

            #def save_dendrogram_as_text(linkage_matrix, labels, output_file):

            # Step 1: Create a mapping of cluster IDs to nodes
            nodes = {}
            next_cluster_id = len(self.linkage_labels)  # Cluster IDs start after the number of leaves
        
            # Initialize leaf nodes
            for i, label in enumerate(self.linkage_labels):
                nodes[i] = Node(label)
                print(label)
        
            # Step 2: Build the tree structure using the linkage matrix
            for row in self.linkage_matrix:
                left_id = int(row[0])  # Left child cluster ID
                right_id = int(row[1])  # Right child cluster ID
                new_cluster_id = next_cluster_id  # New cluster ID
                next_cluster_id += 1
        
                # Create a new parent node for the merged clusters
                parent_node = Node(f"Cluster{new_cluster_id}")
                parent_node.children = [nodes[left_id], nodes[right_id]]
        
                # Update the mapping with the new cluster
                nodes[new_cluster_id] = parent_node
        
            # Step 3: Get the root node (the last cluster created)
            root_node = nodes[next_cluster_id - 1]
        
            # Step 4: Render the tree as an ASCII representation
            with open(savename, "w", encoding="utf-8") as f:
                for pre, _, node in RenderTree(root_node):
                    f.write(f"{pre}{node.name}\n")
        
            
            
            
    def WordCooccurence(self):
        if len(self.df_hasil) == 0: return
        
        self.canvas.setVisible(True)
        #self.toolbar.setVisible(True)
        #self.plot_container.setVisible(False)
        self.scroll_area.setVisible(False) 
        self.tblKataData.setVisible(True)
        
        combined_list = self.df_hasil.apply(lambda row: f"{row['Left']} {row['Right']}", axis=1).tolist()

        # Step 1: Join and extract valid words from combined_list
        text = ' '.join(combined_list)
        
        # Regex to match words including internal hyphen/underscore
        words = re.findall(r'\b\w+(?:[-_]\w+)*\b', text)
        
        # Step 2: Count collocates in window
        window_counts = Counter(words)
        
        # Step 3: Get total frequency of keyword in corpus
        if self.parent.parent.unigrams.empty:
            self.msgBox.setText("The data of unigrams will be created")
            self.msgBox.setWindowTitle("KeyText Version 0.16")
            self.msgBox.setStandardButtons(QMessageBox.Ok)
            self.msgBox.show()
            self.parent.parent.fill_unigrams()
        
        unigrams = self.parent.parent.unigrams
        #print(unigrams.head())
        
        for keyword in self.leCariKata.text().split('|'):
            freq_keyword = 0
            freq_each_word = unigrams.loc[unigrams['Unigram'] == keyword, 'Frequency']
            
            if freq_each_word.empty:
                freq_each_word = 1  # avoid division by zero
            else:
                freq_each_word = freq_each_word.values[0]
            freq_keyword = freq_keyword + freq_each_word
            
        
        # Step 4: Prepare the results
        data = []
        for word, freq_window in window_counts.items():
            if word == keyword:
                continue  # skip the keyword itself
        
            # Frequency in the entire corpus
            freq_corpus = unigrams.loc[unigrams['Unigram'] == word, 'Frequency']
            freq_corpus = freq_corpus.values[0] if not freq_corpus.empty else 1  # assume 1 if not found
        
            # logDice score
            dice_score = 14 + np.log2((2 * freq_window) / (freq_keyword + freq_corpus))
            data.append([word, freq_window, freq_corpus, round(dice_score, 3)])
        
        # Step 5: Create DataFrame
        result_df = pd.DataFrame(data, columns=['Word', 'Freq_in_Window', 'Freq_in_Corpus', 'logDice'])
        
        # Optional: Sort by logDice
        result_df = result_df.sort_values(by='logDice', ascending=False).reset_index(drop=True)
        stopwords = self.parent.parent.stop_words
        if self.rbExcludeStopWords.isChecked():
            result_df = result_df[~result_df['Word'].isin(stopwords)]
        
        self.df_cooccurence = result_df
        # result_df now contains your desired output
        
        # Update the table model
        model = pandasModelKWIC(result_df)
        self.tblKataData.setModel(model)
        self.tblKataData.resizeColumnToContents(1)
        self.tblKataData.setColumnWidth(1, 400)
        self.tblKataData.setColumnWidth(3, 400)
        
        # Update UI
        #self.lbJumlahCuitan.setText('Number of Texts = ' + str(len(self.df_hasil)))
        #self.btReplaceKWIC.setEnabled(True)
        self.tblKataData.setVisible(True)
        
        self.data_representation = "cooccurence"   
    

 
        
        
    def createWordCloud(self):
        if len(self.df_hasil)>0:
            self.canvas.setVisible(True)
            #self.toolbar.setVisible(True)
            #self.plot_container.setVisible(True)
            self.scroll_area.setVisible(True) 
            
            self.tblKataData.setVisible(False)
            combined_list = self.df_hasil.apply(lambda row: f"{row['Left']} {row['Keywords']} {row['Right']}", axis=1).tolist()
            #combined_text = ' '.join(combined_list)
            
            def tokenize(text):
                # Remove all punctuations except underscore and convert text to lower case
                text = re.sub(r'[^\w\s_\-]', '', text).lower()
                # Split text into words
                words = text.split()
                return words
            
            # Step 2: Tokenize all texts and flatten the list of lists into a single list of words
            all_words = [word for text in combined_list for word in tokenize(text)]
            
            if self.rbExcludeSearchWords.isChecked():
                excluded_words = self.parent.parent.stop_words + self.leCariKata.text().split("|")
                #wordcloud = WordCloud(stopwords = excluded_words, width=800, height=400, background_color='white').generate(combined_text)
            else:
                #wordcloud = WordCloud(stopwords = self.parent.parent.stop_words, width=800, height=400, background_color='white').generate(combined_text)
                excluded_words = self.parent.parent.stop_words
            
            # Step 3: Remove stop words
            filtered_words = [word for word in all_words if word not in excluded_words]
            
            # Step 4: Count the frequency of each word
            word_counts = Counter(filtered_words)
            
            # Step 5: Create a DataFrame from the word_counts dictionary
            df_wordcloud = pd.DataFrame(word_counts.items(), columns=['word', 'frequency'])
            
            # Step 6: Sort the DataFrame by frequency in descending order
            df_wordcloud = df_wordcloud.sort_values(by='frequency', ascending=False).reset_index(drop=True)
            
            if len(df_wordcloud) >= 100:
                top_100_words = df_wordcloud.head(100).set_index('word')['frequency'].to_dict()
            else:
                top_100_words = df_wordcloud.set_index('word')['frequency'].to_dict()
            
            wordcloud = WordCloud(width=800, height=400, background_color='white').generate_from_frequencies(top_100_words)

            self.figure.clear()
            self.ax = self.figure.add_subplot(111)
            self.ax.axis('off')
            #self.ax.set_title("Word Cloud")
            self.ax.imshow(wordcloud)
    
            self.canvas.draw()  # Update the canvas
        
            #self.btCooccur.setEnabled(False)
            self.canvas.setVisible(True)
            self.data_wordcloud = df_wordcloud
            self.data_representation = "wordcloud"
        
    def salinKataKata(self):
        self.leCariKata.setText(self.parent.tabComparison.all_words)
        self.parent.tabComparison.all_words = ''
        
        
    
    
    def replaceKWIC(self):
        self.canvas.setVisible(False)
        #self.toolbar.setVisible(False)
        #self.plot_container.setVisible(False)
        self.scroll_area.setVisible(False) 
        
        self.tblKataData.setVisible(True)
        
        kata_yang_dicari = self.leCariKata.text().strip()
        
        #if has_non_alphanumeric(kata_yang_dicari) or len(kata_yang_dicari.split(' ')) == 1:
        #   return
        
        #TO ENSURE THAT ANYTHING CAN BE REPLACED
        '''
        if has_non_alphanumeric(kata_yang_dicari):
            return
        '''
        
        kata_gabungan = '_'.join(kata_yang_dicari.split(' '))
        
        dialog = QDialog()
        dialog.setWindowTitle("Confirmation")
        
        label = QLabel("Replace " + kata_yang_dicari + " with:")
        feedback_input = QLineEdit(kata_gabungan)  # Set default value
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        
        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(feedback_input)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        
        response = dialog.exec_()
        if response != QDialog.Accepted:
            return
        elif kata_yang_dicari == feedback_input.text():
            self.msgBox.setText("There is no replacement")
            self.msgBox.setWindowTitle("TopMod Version 0.42")
            self.msgBox.setStandardButtons(QMessageBox.Ok)
            self.msgBox.show()
            return
        else:            
            df = self.parent.parent.main_data.copy()
            # Use \b to indicate word boundaries so that only whole words are replaced
            df['SelectedColumn'] = df['SelectedColumn'].str.replace(rf'\b{re.escape(kata_yang_dicari)}\b', feedback_input.text(), regex=True)
            
            #df['SelectedColumn'] = df['SelectedColumn'].str.replace(kata_yang_dicari, feedback_input.text())         
            self.parent.parent.main_data = df
            self.parent.parent.main_data_hasbeen_changed = True
            self.parent.parent.main_data_hastobe_saved = True
            self.tblKataData.setVisible(False)
  
        
    def changedWindowSpan(self):
        self.windowSpan = self.sbWindowSpan.value()
        
    def cariKataDiData(self):
        # Compile regex patterns for search phrases
        def build_pattern(search_phrases):
            patterns = []
            for phrase in search_phrases.split('|'):
                phrase = phrase.strip()
                if phrase.startswith("*") and phrase.endswith("*"):
                    pattern = rf"\b\w*{re.escape(phrase[1:-1])}\w*\b"
                elif phrase.startswith("*"):
                    pattern = rf"\b\w*{re.escape(phrase[1:])}\b"
                elif phrase.endswith("*"):
                    pattern = rf"\b{re.escape(phrase[:-1])}\w*\b"
                else:
                    pattern = rf"\b{re.escape(phrase)}\b"
                patterns.append(pattern)
            return re.compile('|'.join(patterns), re.IGNORECASE)
        
        # Function to extract keywords and split text
        def extract_keywords(df, pattern, column):
            # Find the first match using regex
            matches = df[column].str.findall(pattern).str[0]  # Get the first match
            df['Keywords'] = matches
            
            # Split text into Left and Right based on the first match
            split_df = df[column].str.split(pattern.pattern, n=1, expand=True)
            
            # Debugging: Print the structure of split_df
            print("Split DataFrame:")
            print(split_df.head())
            
            # Handle cases where the split does not produce two columns
            df['Left'] = split_df[0] if 0 in split_df.columns else ''
            df['Right'] = split_df[1] if 1 in split_df.columns else ''
            
            return df
    
        # Hide unnecessary UI elements
        self.canvas.setVisible(False)
        #self.toolbar.setVisible(False)
        #self.plot_container.setVisible(False)
        self.scroll_area.setVisible(False) 
        self.tblKataData.setVisible(True)
        self.btSaveData.setVisible(True)
        
        # Build the regex pattern from SearchWord
        regex_pattern = build_pattern(self.leCariKata.text())
        #print(regex_pattern)
        
        # Copy the main data
        df = self.parent.parent.main_data.copy()
        kolom = 'SelectedColumn'
        
        #print('Panjangnya df = ' + str(len(df)))
        
        # Extract keywords and split text
        df = extract_keywords(df, regex_pattern, kolom)
        
        # Filter rows with valid keywords
        self.df_hasil = df[df['Keywords'].notna()]
        #print('Panjangnya df_hasil = ' + str(len(self.df_hasil)))
        
        # Early exit if no matches are found
        if len(self.df_hasil) == 0:
            self.tblKataData.setVisible(False)
            self.msgBox.setText("There is no " + self.leCariKata.text())
            self.msgBox.setWindowTitle("KeyText Version 0.16")
            self.msgBox.setStandardButtons(QMessageBox.Ok)
            self.msgBox.show()
            return
        
        # Apply window span to Left and Right columns
        self.df_hasil['Left'] = self.df_hasil['Left'].str.split().str[-self.windowSpan:].str.join(' ')
        self.df_hasil['Right'] = self.df_hasil['Right'].str.split().str[:self.windowSpan].str.join(' ')
        
        # Process left and right search phrases
        cari_kata_kiri = [kata.strip() for kata in self.leKataKiri.text().split('|') if kata.strip()]
        cari_kata_kanan = [kata.strip() for kata in self.leKataKanan.text().split('|') if kata.strip()]
        
        if cari_kata_kiri and cari_kata_kanan and self.rbAndLeftRight.isChecked():
            #print('cari kiri DAN kanan')
            daftar_cari_kiri = re.compile('|'.join([r'(?<!\w)' + re.escape(kata.replace(r'*', r'\w*')) + r'(?!\w)' for kata in cari_kata_kiri]), re.IGNORECASE)
            daftar_cari_kanan = re.compile('|'.join([r'(?<!\w)' + re.escape(kata.replace(r'*', r'\w*')) + r'(?!\w)' for kata in cari_kata_kanan]), re.IGNORECASE)
            
            self.df_hasil = self.df_hasil[
                self.df_hasil['Left'].str.contains(daftar_cari_kiri) &
                self.df_hasil['Right'].str.contains(daftar_cari_kanan)
            ]
        elif cari_kata_kiri and cari_kata_kanan:
            #print('cari kiri ATAU kanan')
            daftar_cari_kiri = re.compile('|'.join([r'(?<!\w)' + re.escape(kata.replace(r'*', r'\w*')) + r'(?!\w)' for kata in cari_kata_kiri]), re.IGNORECASE)
            daftar_cari_kanan = re.compile('|'.join([r'(?<!\w)' + re.escape(kata.replace(r'*', r'\w*')) + r'(?!\w)' for kata in cari_kata_kanan]), re.IGNORECASE)
            
            self.df_hasil = self.df_hasil[
                self.df_hasil['Left'].str.contains(daftar_cari_kiri) |
                self.df_hasil['Right'].str.contains(daftar_cari_kanan)
            ]
        elif cari_kata_kiri:
            #print('cari kiri saja')
            daftar_cari_kiri = re.compile('|'.join([r'(?<!\w)' + re.escape(kata.replace(r'*', r'\w*')) + r'(?!\w)' for kata in cari_kata_kiri]), re.IGNORECASE)
            self.df_hasil = self.df_hasil[self.df_hasil['Left'].str.contains(daftar_cari_kiri)]
        elif cari_kata_kanan:
            #print('cari kanan saja')
            daftar_cari_kanan = re.compile('|'.join([r'(?<!\w)' + re.escape(kata.replace(r'*', r'\w*')) + r'(?!\w)' for kata in cari_kata_kanan]), re.IGNORECASE)
            self.df_hasil = self.df_hasil[self.df_hasil['Right'].str.contains(daftar_cari_kanan)]
        
        # Early exit if no matches are found after filtering
        if len(self.df_hasil) == 0:
            self.tblKataData.setVisible(False)
            self.msgBox.setText("There is no " + self.leCariKata.text() + ' and ' + self.leKataKiri.text() + ' or ' + self.leKataKanan.text())
            self.msgBox.setWindowTitle("KeyText Version 0.16")
            self.msgBox.setStandardButtons(QMessageBox.Ok)
            self.msgBox.show()
            return
        
        # Update the table model
        model = pandasModelKWIC(self.df_hasil[['Date', 'Left', 'Keywords', 'Right']])
        self.tblKataData.setModel(model)
        self.tblKataData.resizeColumnToContents(1)
        self.tblKataData.setColumnWidth(1, 400)
        self.tblKataData.setColumnWidth(3, 400)
        
        # Update UI
        self.lbJumlahCuitan.setText('Number of Texts = ' + str(len(self.df_hasil)))
        self.btReplaceKWIC.setEnabled(True)
        self.tblKataData.setVisible(True)
        
        self.data_representation = "kwic"   
    

        


class pandasModel(QAbstractTableModel):

    def __init__(self, data):
        QAbstractTableModel.__init__(self)
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parnet=None):
        return self._data.shape[1]
    
    def flags(self, index):
        #return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return str(self._data.iloc[index.row(), index.column()])
        return None
    

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[col]
        return None

class pandasModelKWIC(pandasModel):
    #This additional code to help sorting
    def __init__(self, df, parent=None):
        super().__init__(parent)
        self._data = df
        self._df = df
        
    def sort(self, column, order=Qt.AscendingOrder):
        colname = self._data.columns[column]
        ascending = (order == Qt.AscendingOrder)
        
        self.layoutAboutToBeChanged.emit()
        self._data = self._data.sort_values(by=colname, ascending=ascending).reset_index(drop=True)
        self._df = self._data  # keep both in sync
        self.layoutChanged.emit()

    
    #This additional code to help sorting
    
    def data(self, index, role = Qt.DisplayRole):
        column = index.column()
        row = index.row()

        if role == Qt.DisplayRole:
            return str(self._data.iloc[index.row(), index.column()])
        elif role == Qt.BackgroundRole:
            if index.column() == 2:
                return QBrush(QColor(230,230,230))
                #return QBrush(Qt.green)
            elif index.row() % 2 == 0:
                return QBrush(QColor(240,240,240))
            else:
                return QBrush(Qt.white)
            
            
            #return QColor(Qt.white)
        elif role == Qt.TextAlignmentRole:
            if index.column() == 0:
                return Qt.AlignRight
            if index.column() == 1:
                return Qt.AlignRight   
            elif index.column() == 2:
                return Qt.AlignCenter
            if index.column() == 3:
                return Qt.AlignLeft
            else:
                return Qt.AlignLeft

        return None
    

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[col]
        elif role == Qt.BackgroundRole:
            return QBrush(Qt.green)
        return None
    
class dictionaryModel(QAbstractTableModel):

    def __init__(self, data):
        QAbstractTableModel.__init__(self)
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parnet=None):
        return self._data.shape[1]

    def flags(self, index):
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
    
    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole or role == Qt.EditRole:
                value = self._data.iloc[index.row(), index.column()]
                return str(value)
    

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[col]
        return None
        
    def setData(self, index, value, role=QtCore.Qt.EditRole):
        self._data.iloc[index.row(),index.column()] = value
        self.dataChanged.emit(index, index, (QtCore.Qt.DisplayRole, ))
        return True 
    



class pandasModel(QAbstractTableModel):

    def __init__(self, data):
        QAbstractTableModel.__init__(self)
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]
    
    def flags(self, index):
        #return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
    
    def data(self, index, role=Qt.DisplayRole):
        
        if role == Qt.DisplayRole:
            if index.isValid():
                row = index.row()
                col = index.column()
                return str(self._data.iloc[row, col])
        return None
    
    '''
    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return str(self._data.iloc[index.row(), index.column()])
        return None
    '''

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[col]
        return None
    
#This class to make tableview editable

class MyDelegate(QItemDelegate):

    def createEditor(self, parent, option, index):
        if index.column() == 2:
            return super(MyDelegate, self).createEditor(parent, option, index)
        return None

    def setEditorData(self, editor, index):
        if index.column() == 2:
            # Gets display text if edit data hasn't been set.
            text = index.data(Qt.EditRole) or index.data(Qt.DisplayRole)
            editor.setText(text)

def main():
       
    
    app = QApplication(sys.argv) 
    ex = App() 
    sys.exit(app.exec_()) 
  
if __name__ == '__main__': 
    # Pyinstaller fix
    #multiprocessing.freeze_support()
    
    main()
    
    '''
    app = QApplication(sys.argv) 
    ex = App() 
    sys.exit(app.exec_()) 
    '''
