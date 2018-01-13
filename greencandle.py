#!/usr/bin/python2
# pylint: disable=no-member

"""
Elephant - a System Tray Notification system built with Python2 and pyQT4
Many of the UI components have been taken/adapted from https://github.com/swanson/stacktracker
which is a notification system for stackoverflow.com
"""

from datetime import timedelta, datetime
try:
    import json
except ImportError:
    import simplejson as json

import sys
import signal
import inspect
import logging
import os
import re
import time
import urllib2

from PyQt4 import QtCore, QtGui
from Queue import Queue

import oauth as ops

logger = logging.getLogger("Elephant log")
loggerW = logging.getLogger("Elephant log2")


class QLineEditWithPlaceholder(QtGui.QLineEdit):
    """
        Custom Qt widget that is required since PyQt does not yet
        support Qt4.7 -- which adds native placeholder text functionality to
        QLineEdits
        """
    def __init__(self, parent=None):
        QtGui.QLineEdit.__init__(self, parent)
        self.placeholder = None

    def setPlaceholderText(self, text):
        self.placeholder = text
        self.update()

    def paintEvent(self, event):
        """Overload paintEvent to draw placeholder text under certain conditions"""

        QtGui.QLineEdit.paintEvent(self, event)
        if self.placeholder and not self.hasFocus() and not self.text():
            painter = QtGui.QPainter(self)
            painter.setPen(QtGui.QPen(QtCore.Qt.darkGray))
            painter.drawText(QtCore.QRect(8, 1, self.width(), self.height()), \
                             QtCore.Qt.AlignVCenter, self.placeholder)
            painter.end()

class QuestionDisplayWidget(QtGui.QWidget):
    """Custom Qt Widget to display pretty representations of Question objects"""
    def __init__(self, question, parent=None):
        QtGui.QWidget.__init__(self, parent)

        icons = {
            'ISS':'issue.png',
            'ALM': 'alarms.png',
            'REF': 'unknown.png',
            'Push': 'push.png'
        }

        self.setGeometry(QtCore.QRect(0, 0, 320, 80))
        self.setStyleSheet('QLabel {color: #cccccc;}')
        self.frame = QtGui.QFrame(self)
        self.frame.setObjectName('mainFrame')
        self.frame.setStyleSheet('#mainFrame {background-color: '
                                 'qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, '
                                 'stop: 0 #333333, stop: 1 #4d4d4d);}')

        self.question = question

        font = QtGui.QFont()
        font.setPointSize(14)

        self.question_label = QtGui.QLabel(self.frame)
        self.question_label.setGeometry(QtCore.QRect(10, 7, 280, 50))
        self.question_label.setWordWrap(True)
        self.question_label.setFont(font)
        self.question_label.setText(question.title)
        self.question_label.setObjectName('question_label')
        self.question_label.setStyleSheet("#question_label{color: #83ceea;"
                                          "text-decoration:underline} "
                                          "#question_label:hover{color: "
                                          "#b9eafc;}")
        self.question_label.mousePressEvent = self.launchUrl

        self.remove_button = QtGui.QPushButton(self.frame)
        self.remove_button.setGeometry(QtCore.QRect(295, 7, 25, 25))
        self.remove_button.setText('X')
        self.remove_button.setFont(font)
        self.remove_button.setStyleSheet("QPushButton{background: "
                                         "#818185; border: 3px solid black; "
                                         "color: white; text-align: center;} "
                                         "QPushButton:hover{background: "
                                         "#c03434;}")
        self.remove_button.clicked.connect(self.remove)
        self.answers_label = QtGui.QLabel(self.frame)
        try:
            tags = question.tags[0] + ", " + question.tags[1]
        except:
            tags = question.tags[0]  # If doesn't have more than one tag
        self.answers_label.setText('tags: %s' % tags)  # FIXME: with some value
        self.answers_label.setGeometry(QtCore.QRect(40, 65, 100, 20))
        if question.name is not None:
            self.submitted_label = QtGui.QLabel(self.frame)
            self.submitted_label.setText('Owner: ' + question.name)
            self.submitted_label.setObjectName('submitted_label')
            self.submitted_label.setStyleSheet("#submitted_label{color: "
                                               "#ffffff;text-decoration:"
                                               "underline} #question_label:"
                                               "hover{color: #ffffff;}")
            self.submitted_label.mousePressEvent = self.launchProfile
            self.submitted_label.setAlignment(QtCore.Qt.AlignRight)
            self.submitted_label.setGeometry(QtCore.QRect(120, 65, 200, 20))

        set = False
        for i in question.tags:

            self.site_icon = QtGui.QLabel(self.frame)
            self.site_icon.setGeometry(QtCore.QRect(10, 60, 30, 30))

            if i in icons:
                set = True
                self.site_icon.setStyleSheet("image: url(img/" +
                                             icons[i] +
                                             "); background-repeat:no-repeat;")
                break
        if set == False:
            self.site_icon.setStyleSheet("image: url(img/default.png); "
                                         "background-repeat:no-repeat;")

    def remove(self):
        self.emit(QtCore.SIGNAL('removeQuestion'), self.question)

    def launchUrl(self, event):
        if "https" in self.question.url:
            url_to_open = self.question.url
        else:
            url_to_open = "https://my_company.com/%s" % self.question.url

        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url_to_open))

    def launchProfile(self, event):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(self.question.profile))

class QSpinBoxRadioButton(QtGui.QRadioButton):
    """
        Custom Qt Widget that allows for a spinbox to be used in
        conjunction with a radio button
        """
    def __init__(self, prefix='', suffix='', parent=None):
        QtGui.QRadioButton.__init__(self, parent)
        self.prefix = QtGui.QLabel(prefix)
        self.prefix.mousePressEvent = self.labelClicked
        self.suffix = QtGui.QLabel(suffix)
        self.suffix.mousePressEvent = self.labelClicked

        self.spinbox = QtGui.QSpinBox()
        self.spinbox.setEnabled(self.isDown())
        self.toggled.connect(self.spinbox.setEnabled)

        self.layout = QtGui.QHBoxLayout()
        self.layout.addWidget(self.prefix)
        self.layout.addWidget(self.spinbox)
        self.layout.addWidget(self.suffix)
        self.layout.addStretch(2)
        self.layout.setContentsMargins(25, 0, 0, 0)
        self.setLayout(self.layout)

    def labelClicked(self, event):
        self.toggle()

    def setPrefix(self, p):
        self.prefix.setText(p)

    def setSuffix(self, s):
        self.suffix.setText(s)

    def setSpinBoxSuffix(self, text):
        self.spinbox.setSuffix(" %s" % text)

    def setMinimum(self, value):
        self.spinbox.setMinimum(value)

    def setMaximum(self, value):
        self.spinbox.setMaximum(value)

    def setSingleStep(self, step):
        self.spinbox.setSingleStep(step)

    def value(self):
        return self.spinbox.value()

    def setValue(self, value):
        self.spinbox.setValue(value)

class SettingsDialog(QtGui.QDialog):
    """
        Settings window that allows the user to customize the application
        Currently supports auto-removing questions and changing the refresh
        interval.
        """
    def __init__(self, parent=None):
        self.parent = parent
        QtGui.QDialog.__init__(self, parent)
        self.setFixedSize(QtCore.QSize(400, 450))
        self.setWindowTitle('Settings')
        self.layout = QtGui.QVBoxLayout()
        self.auto_layout = QtGui.QVBoxLayout()

        self.update_interval = QtGui.QGroupBox("Update Interval", self)
        self.update_input = QtGui.QSpinBox()
        self.update_input.setMinimum(15)
        self.update_input.setMaximum(86400)
        self.update_input.setSingleStep(15)
        self.update_input.setSuffix(" seconds")
        self.update_input.setPrefix("Check for updates every ")

        self.update_layout = QtGui.QVBoxLayout()
        self.update_layout.addWidget(self.update_input)

        self.update_interval.setLayout(self.update_layout)

        self.address_group = QtGui.QGroupBox("Source Address", self)
        self.address = QtGui.QLineEdit("http://127.1:80/sample.json", self)
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.address)
        vbox.addStretch(1)
        self.address_group.setLayout(vbox)
        self.layout.addWidget(self.address_group)

        self.notifications = QtGui.QGroupBox("Activate Notifications", self)
        self.notifications.setCheckable(True)
        self.notifications.setChecked(True)
        self.layout.addWidget(self.notifications)

        self.logging = QtGui.QGroupBox("Activate Logging", self)
        self.logging.setCheckable(True)
        self.logging.setChecked(False)
        self.layout.addWidget(self.logging)

        self.test = QtGui.QGroupBox("&Test States", self)
        self.radio1 = QtGui.QRadioButton("B&ad State")
        self.radio2 = QtGui.QRadioButton("Goo&d State")
        self.radio3 = QtGui.QRadioButton("Unknown State")
        self.radio1.setChecked(True)
        self.vbox2 = QtGui.QVBoxLayout()
        self.vbox2.addWidget(self.radio1)
        self.vbox2.addWidget(self.radio2)
        self.vbox2.addWidget(self.radio3)
        self.vbox2.addStretch(1)

        hbox1 = QtGui.QHBoxLayout()
        self.test.setLayout(hbox1)
        test_button = QtGui.QPushButton("Test")
        test_button.clicked.connect(self.test_state)
        hbox1.addLayout(self.vbox2)
        hbox1.addWidget(test_button)
        self.layout.addWidget(self.test)

        self.authToken = QtGui.QGroupBox("Auth Token", self)

        hbox2 = QtGui.QHBoxLayout()
        self.authToken.setLayout(hbox2)
        self.authTokenString = QtGui.QLineEdit("<Token>")
        self.authTokenGet = QtGui.QPushButton("Get Token(Beta)")
        self.authTokenGet.clicked.connect(self.openPage)

        hbox2.addWidget(self.authTokenString)
        hbox2.addWidget(self.authTokenGet)
        self.layout.addWidget(self.authToken)

        self.buttons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Cancel |
                                              QtGui.QDialogButtonBox.Save)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.layout.addWidget(self.update_interval)
        self.layout.addStretch(2)
        self.layout.addWidget(self.buttons)

        self.setLayout(self.layout)
        self.loadSettings()

    def openPage(self):
        token = ops.login()
        self.authTokenString.setText(token)

    def showDialog(self):
        text, ok_status = QtGui.QInputDialog.getText(self, 'Input Dialog',
                                              'Paste Full Web Address here:')

        if ok_status:
            self.authTokenString.setText(str(text))

    def test_state(self):
        qvbl = self.vbox2.layout()
        for i in range(0, qvbl.count()):
            widget = qvbl.itemAt(i).widget()
            if (widget != 0) and (type(widget) is QtGui.QRadioButton):
                if widget.isChecked():
                    if i == 0:
                        #self.run="true"
			self.parent.notify_bad()
                        #self.parent.constant()
                    elif i == 1:
                        self.parent.notify_good()
                    else:
                        self.parent.notify_unknown()

    def updateSettings(self, settings):
        """Restore saved settings from a dictionary"""
        singleton = Singleton()

        try:
            self.address.setText(settings['address'])
        except:
            return
        try:
            if settings['notifications']:
                self.notifications.setChecked(True)
                singleton.notify = True
            else:
                self.notifications.setChecked(False)
                singleton.notify = False
        except:
            self.notifications.setChecked(True)
            singleton.notify = True
        try:
            self.authTokenString.setText(settings['auth'])
        except:
            return
        try:
            if settings['logging']:
                self.logging.setChecked(True)
                singleton.logging = True
            else:
                self.logging.setChecked(False)
            singleton.logging = False
        except:
            self.logging.setChecked(False)
            singleton.logging = False

    def loadSettings(self):
        try:
            with open(os.environ['HOME'] + '/.elephantrc', 'r') as file_handle:
                data = file_handle.read()
                file_handle.close()
        except EnvironmentError:
            return
        self.updateSettings(json.loads(data))

    def getSettings(self):
        """Returns a dictionary of currently selected settings"""
        settings = {}
        settings['update_interval'] = self.update_input.value()
        settings['address'] = str(self.address.text())
        settings['auth'] = str(self.authTokenString.text())
        settings['notifications'] = self.notifications.isChecked()
        settings['logging'] = self.logging.isChecked()
        return settings

class Singleton:
    """ A python singleton """
    lastSuccessfull = 'None'
    update_color = 'red'
    state_color = ['green', 'yellow', 'red', 'black'] # 0, 1, 2, 3
    remove_list = []
    class __impl:
        """ Implementation of the singleton interface """

        def spam(self):
            """ Test method, return singleton id """
            return id(self)

    # storage for the instance reference
    __instance = None

    def __init__(self):
        """ Create singleton instance """
        # Check whether we already have an instance
        if Singleton.__instance is None:
            # Create and remember instance
            Singleton.__instance = Singleton.__impl()

        # Store instance reference as the only member in the handle
        self.__dict__['_Singleton__instance'] = Singleton.__instance

    def __getattr__(self, attr):
        """ Delegate access to implementation """
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        """ Delegate access to implementation """
        return setattr(self.__instance, attr, value)

class Events(object):
    """Application specific representation of an event"""
    def __init__(self, id, name, unixname, email, title, creation_time, url,
                 types, profile):
        self.id = id
        self.unixname = unixname
        self.url = url
        self.title = title
        self.profile = profile
        self.name = name
        self.tags = []
        self.tags.append(types)

        if len(self.title) > 69:
            self.title = self.title[:69] + '...'
        if creation_time is None:
            self.creation_time = datetime.utcnow()
        else:
            self.creation_time = datetime.utcfromtimestamp(creation_time)

    def __repr__(self):
        return "%s: %s" % (self.id, self.title)

    def __eq__(self, other):
        try:
            return (self.unixname == other.unixname) and (self.id == other.id)
        except:
            return ("unixname") and (9999)

class Question(object):
    """Application specific representation of a StackExchange question"""
    def __init__(self, question_id, site, title=None, created=None, \
                 last_queried=None, already_answered=None, \
                 answer_count=None, submitter=None):
        self.id = question_id
        self.site = site

        api_base = 'http://api.%s/%s' \
            % (self.site, APIHelper.API_VER)
        base = 'http://%s/questions/' % (self.site)
        self.url = base + self.id

        self.json_url = '%s/questions/%s/%s' \
            % (api_base, self.id, APIHelper.API_KEY)

        if title is None or answer_count is None or submitter is None or already_answered is None:
            so_data = APIHelper.callAPI(self.json_url, self.auth)

        if title is None:
            self.title = so_data['questions'][0]['title']
        else:
            self.title = title

        if already_answered is None:
            self.already_answered = 'accepted_answer_id' in so_data['questions'][0]
        else:
            self.already_answered = already_answered

        if answer_count is None:
            self.answer_count = so_data['questions'][0]['answer_count']
        else:
            self.answer_count = answer_count

        if submitter is None:
            try:
                self.submitter = so_data['questions'][0]['owner']['display_name']
            except KeyError:
                self.submitter = None
        else:
            self.submitter = submitter

        if len(self.title) > 45:
            self.title = self.title[:43] + '...'

        if last_queried is None:
            self.last_queried = datetime.utcnow()
        else:
            self.last_queried = datetime.utcfromtimestamp(last_queried)

        if created is None:
            self.created = datetime.utcnow()
        else:
            self.created = datetime.utcfromtimestamp(created)

        self.answers_url = '%s/questions/%s/answers%s&min=%s' \
            % (api_base, self.id, APIHelper.API_KEY,
               int(calendar.timegm(self.created.timetuple())))

        self.comments_url = '%s/questions/%s/comments%s&min=%s' \
            % (api_base, self.id, APIHelper.API_KEY,
               int(calendar.timegm(self.created.timetuple())))

    def __repr__(self):
        return "%s: %s" % (self.id, self.title)

    def __eq__(self, other):
        return ((self.site == other.site) and (self.id == other.id))

class Notification(object):
    def __init__(self, msg, url=None):
        self.msg = msg
        self.url = url

class Elephant(QtGui.QDialog):
    """
        The 'main' dialog window for the application.  Displays
        the list of tracked questions and has the input controls for
        adding new questions.
        """
    def my_logging(self, text):
        singleton = Singleton()
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        message = "%s - %s" %(calframe[1][3], text)
        if singleton.logging:
            logger.info(message)

    def __call__(self, Parent=None):
        self.my_logging("called")

    def __init__(self, parent=None):
        singleton = Singleton()
        singleton.notify = False
        logger = logging.getLogger("Elephant log")
        filename = "%s/elephant.log" % os.environ['HOME']
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s;%(levelname)s;%(message)s",
                              "%Y-%m-%d %H:%M:%S")
        fh = logging.FileHandler(filename)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        singleton = Singleton()
        singleton.state = 4 #random number
        self.run = "false"
        self.notifications = 1
        self.status = "black"
        self.ctimer = QtCore.QTimer()
        QtCore.QObject.connect(self.ctimer, QtCore.SIGNAL("timeout()"),
                               self.constant_update)
        self.iconIterations = 0
        QtGui.QDialog.__init__(self)
        self.parent = parent
        self.setWindowTitle("Elephant - Status")
        self.closeEvent = self.cleanUp
        self.setStyleSheet("QDialog{background: #f0ebe2;}")

        self.settings_dialog = SettingsDialog(self)
        self.settings_dialog.accepted.connect(self.serializeSettings)
        self.settings_dialog.accepted.connect(self.apply_settings)
        self.settings_dialog.rejected.connect(self.deserializeSettings)
        self.deserializeSettings()

        self.setGeometry(QtCore.QRect(0, 0, 350, 350))   #height, length,
        self.setFixedSize(QtCore.QSize(350, 400))

        self.display_list = QtGui.QListWidget(self)
        self.display_list.resize(QtCore.QSize(350, 400))
        self.display_list.setStyleSheet("QListWidget{show-decoration-selected:"
                                        " 0; background: black;}")
        self.display_list.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.display_list.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.display_list.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.display_list.clear()

        self.updated = QtGui.QLabel(self)
        self.updated.setText(str('Last Successful Update: ' +
                             Singleton.lastSuccessfull))
        self.updated.setGeometry(QtCore.QRect(15, 360, 240, 30))
        self.updated.setStyleSheet("QLabel {font-size : 12px; color : green; }");

        path = os.getcwd()
        icon = QtGui.QIcon(path + '/img/elephant.png')
        self.setWindowIcon(icon)

        self.tracking_list = []
        self.remove_list = []
        self.tracking_list_new = []
        self.displayQuestions()

        self.queue_timer = QtCore.QTimer(self)
        self.queue_timer.timeout.connect(self.process_queue)
        self.notify_queue = Queue()

        icon2 = QtGui.QIcon(path + '/img/elephant.png')
        self.notifier = QtGui.QSystemTrayIcon(icon2, self)
        self.notifier.messageClicked.connect(self.popupClicked)
        self.notifier.activated.connect(self.trayClicked)
        self.notifier.setToolTip('Elephant')

        self.tray_menu = QtGui.QMenu()
        self.show_action = QtGui.QAction('Show', None)
        self.show_action.triggered.connect(self.showWindow)
        self.settings_action = QtGui.QAction('Settings', None)
        self.settings_action.triggered.connect(self.showSettings)

        self.clear_action = QtGui.QAction('Clear Ignore List', None)
        self.clear_action.triggered.connect(self.clear_list)

        self.about_action = QtGui.QAction('About', None)
        self.about_action.triggered.connect(self.show_about)

        self.exit_action = QtGui.QAction('Exit', None)
        self.exit_action.triggered.connect(self.exitFromTray)

        self.tray_menu.addAction(self.show_action)
        self.tray_menu.addAction(self.settings_action)
        self.tray_menu.addAction(self.clear_action)
        self.tray_menu.addAction(self.about_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.exit_action)
        self.notifier.setContextMenu(self.tray_menu)
        self.notifier.show()
        self.worker = WorkerThread(self)
        self.connect(self.worker, QtCore.SIGNAL('updateQuestion'), self.updateQuestion)
        self.connect(self.worker, QtCore.SIGNAL('autoRemove'), self.removeQuestion)
        self.connect(self.worker, QtCore.SIGNAL('done'), self.start_queue_process)
        self.apply_settings()
        self.worker.start()

    def apply_settings(self):
        """Send new settings to worker thread"""
        singleton = Singleton()
        settings = self.settings_dialog.getSettings()
        interval = settings['update_interval'] * 1000 #convert to milliseconds
        self.worker.set_interval(interval)
        self.worker.apply_settings(settings)
        singleton.logging = settings['logging']
        singleton.notif = settings['notifications']


    def trayClicked(self, event):
        """Shortcut to show list of question, not supported in Mac OS X"""
        if event == QtGui.QSystemTrayIcon.DoubleClick:
            self.showWindow()

    def showWindow(self):
        """Show the list of tracked questions"""
        self.show()
        self.showMaximized()
        self.displayQuestions()

    def showSettings(self):
        """Show the settings dialog"""

        self.settings_dialog.show()
    def constant(self):
        self.run = "true"
        self.ctimer.start(600)

    def constant_update(self):
        max_iterations = 31
        singleton = Singleton()

        self.my_logging("-" * 30 + "%s " % singleton.state_color[singleton.new_state])
        if self.iconIterations < max_iterations and self.run == "true":
            self.iconIterations = self.iconIterations + 1

            if self.status == singleton.state_color[singleton.new_state]:
                self.status = "blank"
            elif self.status == "blank":
                self.status = singleton.state_color[singleton.new_state]
            else:
                self.status = "blank"

            path = os.getcwd()
            iconvar = '%s/img/elephant-%s.png' % (path, self.status)
            self.my_logging(iconvar)
            self.notifier.setIcon(QtGui.QIcon(iconvar))
        else:
            self.ctimer.stop()
            self.iconIterations = 0
            self.run = "false"
            path = os.getcwd()
            self.status = singleton.state_color[singleton.new_state]
            iconvar = '%s/img/elephant-%s.png' % (path, self.status)
            self.notifier.setIcon(QtGui.QIcon(iconvar))

    def notify_good(self):
        self.ctimer.stop()
        path = os.getcwd()
        self.my_logging("notify good")
        icon2 = QtGui.QIcon(path + '/img/elephant-green.png')
        self.notifier.setIcon(icon2)
        self.displayQuestions()

    def notify_bad(self):
        path = os.getcwd()
        self.my_logging("notify bad")
        icon2 = QtGui.QIcon(path + '/img/elephant-red.png')
        self.notifier.setIcon(icon2)
        self.displayQuestions()
        my_msg = "Alert: Bad State Test"
        self.notifier.showMessage("Elephant-Test", my_msg, 2000)

    def notify_unknown(self):
        path = os.getcwd()
        self.my_logging("notify unknown")
        icon2 = QtGui.QIcon(path + '/img/elephant.png')
        self.notifier.setIcon(icon2)
        my_msg = "Alert: Unable to Extract JSON"
        self.notifier.showMessage("Elephant-Test", my_msg, 2000)

    def clear_list(self):
        singleton = Singleton()
        singleton.remove_list[:] = []

    def show_about(self):
        """Show About Page, as if anyone actually cares about who made this..."""

        text = """<h3>Elephant</h3>
                  <p>A desktop notifier for large systems build
                  with PyQt4</p>
                  <p>Get customized alerts on what your team is monitoring
                  direct</p>
                  <p><b>Created by Amro Diab adiab@hotmail.co.uk</b></p>
               """
        QtGui.QMessageBox(QtGui.QMessageBox.Information, "About", text).exec_()

    def show_error(self, text):
        """
            Pop-up an error box with a message

            params:
            text => msg to display
            """
        QtGui.QMessageBox(QtGui.QMessageBox.Critical, "Error!", text).exec_()

    def exitFromTray(self):
        """Event handler for 'Exit' menu option"""
        self.serializeSettings()
        self.parent.exit()

    def cleanUp(self, event):
        """Perform last-minute operations before exiting"""
        self.serializeSettings()


    def serializeSettings(self):
        """Persist application settings in external JSON file"""
        settings = self.settings_dialog.getSettings()
        with open(os.environ['HOME'] + '/.elephantrc', 'w') as file_handle:
            json.dump(settings, file_handle, indent = 4)

    def deserializeSettings(self):
        """Restore saved application settings from external JSON file"""
        try:
            with open('settings.json', 'r') as file_handle:
                data = file_handle.read()
        except EnvironmentError:
            #no saved settings, return silently
            return

        self.settings_dialog.updateSettings(json.loads(data))

    def updateQuestion(self, question, status, new_item):
        """
        Update questions in the tracking list with data fetched
        from worker thread
        """

        self.my_logging("running updatequestion")
        self.my_logging(len(self.tracking_list))
        self.my_logging("new item: "+ str(new_item))
        if new_item != 0:
            sys.stderr.write("AMROX HERE!")
            if len(question.title) > 40:
                question.title = question.title[:40] + '...'
            self.add_to_notification_queue(Notification("New event: %s" \
                                                    % question.title))
            self.my_logging("new_answer so adding to queue %s" % question.title)
        if status == 0:
            self.my_logging("status is 0")

        self.displayQuestions()

    def popupClicked(self):
        """Open the question in user's default browser"""
        if self.popupUrl:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl(self.popupUrl))

    def displayQuestions(self):
        self.updated.setText(str('Last Successful Update:\n ' +
                             Singleton.lastSuccessfull))
        sscolor = ("QLabel {font-size : 12px; color : %s; }" %
                   Singleton.update_color)
        self.updated.setStyleSheet(sscolor)
        self.display_list.clear()
        """Render the currently tracked questions in the display list"""

        #hack to fix random disappearing questions
        self.display_list = QtGui.QListWidget(self)
        self.display_list.resize(QtCore.QSize(350, 350))
        self.display_list.setStyleSheet("QListWidget{show-decoration-selected:"
                                        " 0; background: black;}")
        self.display_list.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.display_list.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self.display_list.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.display_list.clear()
        #/end hack

        for question in self.tracking_list:
            item = QtGui.QListWidgetItem(self.display_list)
            item.setSizeHint(QtCore.QSize(320, 95))
            self.display_list.addItem(item)
            qitem = QuestionDisplayWidget(question)
            self.connect(qitem, QtCore.SIGNAL('removeQuestion'),
                         self.removeQuestion)
            self.display_list.setItemWidget(item, qitem)
            del item

        self.display_list.show()

    def removeQuestion(self, q, notify=False):
        """
            Remove a question from the tracking list

            params:
            notify => indicate if the user should be alerted that the
            question is no longer being tracked, useful for
            auto-removing
            """
        singleton = Singleton()

        for question in self.tracking_list[:]:
            if question == q:
                self.tracking_list.remove(question)
                singleton.remove_list.append(q.id)
                if notify:
                    self.add_to_notification_queue(Notification("No longer tracking: %s" \
                                                             % question.title))
                break
        self.displayQuestions()

    def extractDetails(self, url):
        """Strip out the site domain from given URL"""
        #todo: consider using StackAuth
        regex = re.compile("""(?:http://)?(?:www\.)?
            (?P<site>(?:[A-Za-z\.])*\.[A-Za-z]*)
            /.*?
            (?P<id>[0-9]+)
            /?.*""", re.VERBOSE)
        match = regex.match(url)
        if match is None:
            return None
        try:
            site = match.group('site')
            id = match.group('id')
        except IndexError:
            return None
        return id, site

    def addQuestion(self):
        """
        Add a new question to the list of tracked questions and render
        it on the display list
        """
        sys.stderr.write("ADDING QUESTION\n")
        url = self.question_input.text()
        self.question_input.clear()
        details = self.extractDetails(str(url))
        singleton = Singleton()

        if details:
            id, site = details
        else:
            self.show_error("Invalid URL format, please try again.")
            return
        question = Question(id, site)
        sys.stderr.write(question)
        if question not in self.tracking_list and question.id not in singleton.remove_list:

            question = Question(id, site)
            self.tracking_list.append(question)
            self.displayQuestions()
        else:
            self.show_error("This item is already being tracked.")
            return

    def add_to_notification_queue(self, notification):
        self.my_logging("adding to queue")
        self.notify_queue.put(notification)

    def start_queue_process(self):
        if not self.queue_timer.isActive():
            self.queue_timer.start(5000)
            self.process_queue()

    def process_queue(self):
        singleton = Singleton()
        self.my_logging("processq state: %s, new_state: %s "
                        % (singleton.state, singleton.new_state))

        while not self.notify_queue.empty():
            self.my_logging("about to call notiy, %s" % self.notify_queue.qsize())
            if singleton.notify:
                self.notify(self.notify_queue.get())
            else:
                self.my_logging(self.notify_queue.get())
        self.my_logging("end of while not loop")
        if singleton.state != singleton.new_state and singleton.new_state != 0:
            self.flash_icon()
        if self.queue_timer.isActive():
            self.queue_timer.stop()
            singleton.state = singleton.new_state
        if singleton.new_state == 0:
            self.notify_good()


    def notify(self, notification):

        self.my_logging("calling notify.....")
        self.notifier.showMessage("Elephant", notification.msg, 20000)

    def flash_icon(self):
        self.my_logging("called flashicon")
        self.run="true"
        self.constant()

class APIHelper(object):
    """Helper class for API related functionality"""

    API_KEY = '?key=Jv8tIPTrRUOqRe-5lk4myw'
    API_VER = '1.0'

    @staticmethod
    def callAPI(url, auth):
        now = datetime.now()
        singleton = Singleton()
        Singleton.lastSuccessfull = now.strftime("%Y-%m-%d %H:%M")

        fullurl = "%s?access_token=%s" % (url, auth)
        # Make an API call, decompress the gzipped response
        # return json object

        req = urllib2.Request(fullurl, None, {'user-agent':'syncstream/vimeo'})
        opener = urllib2.build_opener()
        try:
            file_handle = opener.open(req, timeout=10)
            Singleton.update_color = 'green'
            return json.load(file_handle)

        except:
            print "req:%s" % fullurl
            print "Unable to fetch live data"
            json_data = open('./unknown.json')
            singleton.new_state = 3
            Singleton.update_color = 'black'
            return json.load(json_data)


    def my_logging(self, text):
        singleton=Singleton()
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        message = "%s - %s" %(calframe[1][3], text)
        if singleton.logging:
            loggerW.info(message)

class ChangeIcon(QtCore.QThread):
    procDone = QtCore.pyqtSignal(bool)
    procPartDone = QtCore.pyqtSignal(int)


    def __init__(self, parent, state):
        from time import sleep
        path = os.getcwd()
        icon2 = QtGui.QIcon(path + '/img/elephant-bad.png')
        icon = QtGui.QIcon(path + '/img/elephant-bad.png')
        for _ in range(1, 10):
            parent.notifier.setIcon(icon)
            sleep(0.5)
            parent.notifier.setIcon(icon2)

class WorkerThread(QtCore.QThread):
    def __init__(self, tracker, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.tracker = tracker
        self.interval = 300000
        self.settings = {}
        filename = "%s/elephant.log" % os.environ['HOME']
        loggerW.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s;%(levelname)s;%(message)s",
                              "%Y-%m-%d %H:%M:%S")
        file_handle = logging.FileHandler(filename)
        file_handle.setFormatter(formatter)
        loggerW.addHandler(file_handle)

    def my_logging(self, text):
        singleton = Singleton()
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        message = "%s - %s" %(calframe[1][3], text)
        if singleton.logging:
            loggerW.info(message)

    def run(self):
        self.timer = QtCore.QTimer()
        self.connect(self.timer, QtCore.SIGNAL('timeout()'), self.fetch,
                     QtCore.Qt.DirectConnection)
        self.timer.start(self.interval)
        try:
            self.fetch()
        except:
            print
        self.exec_()

    def __del__(self):
        self.exit()
        self.terminate()

    def set_interval(self, value):
        self.interval = value

    def apply_settings(self, settings):
        self.settings = settings

    def fetch(self):
        self.my_logging("fetching data...")
        settings = self.settings
        singleton = Singleton()

        self.tracker.tracking_list_new=[]
        address = settings['address']
        auth = settings['auth']

        so_data = APIHelper.callAPI(address, auth)
        self.my_logging("address:%s, auth:%s" %(address, auth))
        event_list = []

        stories_data = so_data["stories"]["events"]
        events_data = so_data["events"]

        for event in stories_data:
            event_list.append(event)
        self.my_logging("%d number of items in list" % len(events_data))
        for e in event_list:
            """ Go through events and extract relevent details """
            event = events_data[str(e)]
            id = e
            name = 'amro diab'
            profile = event['event']
            self.my_logging(event)
            self.my_logging("Failed to get user details for %s" % name)
            profile = "www.google.com"

            unixname = 'adiab'
            email = 'adiab@hotmail.co.uk'
            title = event['symbol']
            creation_time = event['time']
            url = event['url']
            id = e
            types = event['event']
            rebuild_question = Events(id, name, unixname, email, title,
                                      creation_time, url, types, profile)
            self.my_logging("Finish time in epoch: xxx -%s- " % event['time'])
            current_time = time.time()
            self.my_logging("current_time = " + str(current_time))

        self.tracker.tracking_list_new.append(rebuild_question)
        set1 = set((x.id, x.name) for x in self.tracker.tracking_list)
        difference = [x for x in self.tracker.tracking_list_new
                      if (x.id, x.name) not in set1]
        self.my_logging(difference)
        self.my_logging(len(difference))

        for line in difference:
            singleton.new_state = 2
            status = 2
            new_item = 1
            self.my_logging("adding a difference %s" % line)
            self.my_logging("%s %s" % (line.id, line.name))
            self.my_logging("%s %s" % (len(self.tracker.tracking_list),
                                       len(difference)))
            self.emit(QtCore.SIGNAL('updateQuestion'), line, status, new_item)

        self.tracker.tracking_list = self.tracker.tracking_list_new
        self.tracker.tracking_list_new = []

        if len(self.tracker.tracking_list) == 0:
            sys.stderr.write("zero items\n")
            """ If no new questions """
            self.my_logging("no new items")
            self.emit(QtCore.SIGNAL('notify_good'))
            singleton.new_state = 0
            self.my_logging( "this should be 0 %s" % singleton.new_state)
            self.emit(QtCore.SIGNAL('updateQuestion'), 1, 0, 0)

        self.emit(QtCore.SIGNAL('done'))
        self.my_logging("%s %s" %(len(self.tracker.tracking_list),
                                  len(difference)))

    def auto_remove_questions(self):
        if self.settings['auto_remove']:
            if self.settings['on_inactivity']:
                threshold = timedelta(hours = self.settings['on_inactivity'])
                for question in self.tracker.tracking_list[:]:
                    if datetime.utcnow() - question.last_queried > threshold:
                        self.emit(QtCore.SIGNAL('autoRemove'), question, True)
            elif self.settings['on_time']:
                threshold = timedelta(hours = self.settings['on_time'])
                for question in self.tracker.tracking_list[:]:
                    if datetime.utcnow() - question.created > threshold:
                        self.emit(QtCore.SIGNAL('autoRemove'), question, True)

if __name__ == "__main__":
    try:

        signal.signal(signal.SIGINT, signal.SIG_DFL)
        app = QtGui.QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        st = Elephant(app)
        app.exec_()
        del st
        sys.exit()
    except KeyboardInterrupt:
        sys.exit(3)
