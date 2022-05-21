#
# Display the most valuables bodies in a current system, using https://www.edsm.net/ API
#

# from __future__ import print_function
import requests
import sys
import threading
import logging
import os

try:
    # Python 2
    from urllib2 import quote
    import Tkinter as tk
except ModuleNotFoundError:
    # Python 3
    from urllib.parse import quote
    import tkinter as tk

# from ttkHyperlinkLabel import HyperlinkLabel
import myNotebook as nb

from helpers.dbHelper import dbHelper

# if __debug__:
#     from traceback import print_exc

from config import config
from config import appname
from theme import theme

logger = logging.getLogger(
    f'{appname}.{os.path.basename(os.path.dirname(__file__))}')

VERSION = '1.0'

this = sys.modules[__name__]  # For holding module globals
this.frame = None
this.edsm_session = None
this.bodies = None
this.currentSystem = None

# Used during preferences
this.settings = None
this.edsm_setting = None
this.db = None


def plugin_start3(plugin_dir):
    return plugin_start()


def plugin_start():
    logger.info('Starting plugin')
    this.db = dbHelper(logger)
    return 'MostValued'


def plugin_app(parent):
    # Create and display widgets
    this.frame = tk.Frame(parent)

    # callback when EDSM data received
    this.frame.bind('<<NewData>>', processData)

    tHead = tk.Frame(this.frame, name='table_head')
    row = tHead.grid_size()[1]
    # Columns Sizes
    tHead.columnconfigure(0, weight=2)
    tHead.columnconfigure(1, weight=4)
    tHead.columnconfigure(2, weight=2)

    # Create labels
    name = tk.Label(tHead, text='Name')
    value = tk.Label(tHead, text='Value')
    distance = tk.Label(tHead, text='Distance')

    # Grid
    name.grid(row=row, column=0, sticky='W')
    value.grid(row=row, column=1, sticky='WE')
    distance.grid(row=row, column=2, sticky='E')

    tHead.pack(fill='both', expand=True)
    # Main frame can't be empty or it doesn't resize
    this.spacer = tk.Frame(this.frame)
    return this.frame


def plugin_prefs(parent, cmdr, is_beta):
    frame = nb.Frame(parent)
    nb.Label(frame, text='Version %s' % VERSION).grid(
        padx=10, pady=10, sticky=tk.W)

    return frame


def prefs_changed(cmdr, is_beta):
    row = None


def journal_entry(cmdr, is_beta, system, station, entry, state):
    logger.info(entry)
    if entry['event'] == 'SAAScanComplete':
        addScannedBody(entry['BodyName'], system)
        updateRowColorByBodyName(entry['BodyName'], 'green')

    # if entry['event'] == 'SellExplorationData':
    # {'timestamp': '2022-05-21T22:46:41Z', 'event': 'SellExplorationData', 'Systems': ['HR 3404'], 'Discovered': [], 'BaseValue': 2035, 'Bonus': 0, 'TotalEarnings': 2035}

    if entry['event'] in ['Location', 'FSDJump']:
        thread = threading.Thread(
            target=getDataFromEDSM, name='EDSM worker', args=(entry['StarSystem'],))
        thread.daemon = True
        thread.start()


def cmdr_data(data, is_beta):
    # Manual Update
    logger.info('manual update')
    thread = threading.Thread(
        target=getDataFromEDSM, name='EDSM worker', args=(data['lastSystem']['name'],))
    thread.daemon = True
    thread.start()


# EDSM lookup
def getDataFromEDSM(systemName):
    logger.info('getDataFromEDSM')
    if not this.edsm_session:
        this.edsm_session = requests.Session()
    # systemName = 'Bleia Dryiae DY-F d12-3'
    this.currentSystem = systemName
    this.bodies = getSystemBodies(systemName)

    # Tk is not thread-safe, so can't access widgets in this thread.
    # event_generate() is the only safe way to poke the main thread from this thread.
    this.frame.event_generate('<<NewData>>', when='tail')


def sendRequest(url):
    logger.debug('REST Request: '+str(url))
    try:
        r = this.edsm_session.get(url, timeout=10)
        r.raise_for_status()
        data = r.json() or {}  # Unknown system represented as empty list
        logger.info('REST Response: '+str(data))
    except:
        data = {}

    return data


def getSystemBodies(systemName):
    url = 'https://www.edsm.net/api-system-v1/estimated-value?systemName=%s' % quote(
        systemName)
    r = sendRequest(url)
    data = {}
    if r:
        data = r.get("valuableBodies")
        names = []
        response = []
        if data:
            for item in data:
                names.append(item['bodyName'])
            response = getScannedBodies(names)

        for item in data:
            item['scanned'] = False
            if item['bodyName'] in response:
                item['scanned'] = True
    return data


def getNameOfBody(name, systemName):
    return name.replace(systemName+' ', '')


# EDSM data received
def processData(event):

    systemName = this.currentSystem
    # systemName = 'Bleia Dryiae DY-F d12-3'

    tBody = tk.Frame(this.frame, name='table_body')

    for body in this.bodies:

        tRow = tk.Frame(tBody, name=body['bodyName'].replace(' ', '-').lower())
        # Columns Sizes
        tRow.columnconfigure(0, weight=1)
        tRow.columnconfigure(1, weight=4)
        tRow.columnconfigure(2, weight=1)
        row = tRow.grid_size()[1]

        # Data
        nameText = getNameOfBody(body['bodyName'], systemName)
        valueText = "${:,.2f}".format(body['valueMax'])
        distanceText = str(body['distance']) + ' ls'

        # Create labels
        name = tk.Label(tRow, text=nameText, name='name')
        value = tk.Label(tRow, text=valueText, name='value')
        distance = tk.Label(tRow, text=distanceText, name='distance')

        # Grid
        name.grid(row=row, column=0, sticky='w')
        value.grid(row=row, column=1, sticky='WE')
        distance.grid(row=row, column=2, sticky='E')

        if body['distance'] > 25000:
            name.configure(fg='red')
            value.configure(fg='red')
            distance.configure(fg='red')

        if body['scanned']:
            name.configure(fg='green')
            value.configure(fg='green')
            distance.configure(fg='green')

        tRow.pack(fill='both', expand=True)
        theme.update(tRow)

    tBody.pack(fill='both', expand=True)
    theme.update(tBody)


def addScannedBody(name, systemName):
    this.db.execute(
        'INSERT INTO scanned (name, system) VALUES (?,?)', (name, systemName))


def getScannedBodies(names):
    response = []
    params = '?,'*len(names)
    if params[-1] == ',':
        params = params[:-1]
    for item in this.db.execute('SELECT name FROM scanned WHERE name IN ({});'.format(params), names):
        response.append(item[0])
    return response


def updateRowColorByBodyName(name, color):
    for frames in this.frame.winfo_children():
        frameName = str(frames).rpartition('.')[-1]
        logger.debug(frameName)
        if frameName == 'table_body':
            for bodyFrames in frames.winfo_children():
                bodyFrameName = str(bodyFrames).rpartition('.')[-1]
                logger.debug(bodyFrameName)
                # body['bodyName'].replace(' ', '-').lower()
                if bodyFrameName == name.replace(' ', '-').lower():
                    for item in bodyFrames.winfo_children():
                        itemName = str(item).rpartition('.')[-1]
                        logger.debug(itemName)
                        item.configure(fg=color)
