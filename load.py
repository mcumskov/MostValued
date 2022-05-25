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
    logger.debug(entry)
    if entry['event'] == 'SAAScanComplete':
        addScannedBody(entry['BodyName'], system)
        updateRowColorByBodyName(entry['BodyName'], 'green')

    # if entry['event'] == 'SellExplorationData':
    # {'timestamp': '2022-05-21T22:46:41Z', 'event': 'SellExplorationData', 'Systems': ['HR 3404'], 'Discovered': [], 'BaseValue': 2035, 'Bonus': 0, 'TotalEarnings': 2035}

    #{'timestamp': '2022-05-24T22:15:18Z', 'event': 'MultiSellExplorationData', 'Discovered': [OrderedDict([('SystemName', 'Trianguli Sector UO-R b4-2'), ('NumBodies', 4)]), OrderedDict([('SystemName', 'Tribeb'), ('NumBodies', 12)]), OrderedDict([('SystemName', 'Crucis Sector KH-V b2-2'), ('NumBodies', 1)]), OrderedDict([('SystemName', 'Sahun'), ('NumBodies', 6)]), OrderedDict([('SystemName', 'Antliae Sector FL-Y b2'), ('NumBodies', 2)]), OrderedDict([('SystemName', 'Tascheter Sector AG-O a6-0'), ('NumBodies', 1)]), OrderedDict([('SystemName', 'Trianguli Sector TU-O a6-0'), ('NumBodies', 6)]), OrderedDict([('SystemName', 'Trianguli Sector BM-L a8-0'), ('NumBodies', 1)]), OrderedDict([('SystemName', 'Crucis Sector CQ-Y c23'), ('NumBodies', 2)]), OrderedDict([('SystemName', 'EGM 559'), ('NumBodies', 7)]), OrderedDict([('SystemName', 'Xuanebuth'), ('NumBodies', 2)]), OrderedDict([('SystemName', 'Col 285 Sector FQ-O c6-25'), ('NumBodies', 1)]), OrderedDict([('SystemName', 'Sakaja'), ('NumBodies', 3)]), OrderedDict([('SystemName', 'LP 437-12'), ('NumBodies', 1)]), OrderedDict([('SystemName', 'Puppis Sector RD-T b3-3'), ('NumBodies', 2)]), OrderedDict([('SystemName', 'Sharru Sector CV-Y b3'), ('NumBodies', 5)]), OrderedDict([('SystemName', 'Shui Wei Sector ZE-Z b3'), ('NumBodies', 1)]), OrderedDict([('SystemName', 'Hakkaia'), ('NumBodies', 1)]), OrderedDict([('SystemName', 'Alrai Sector KN-S b4-4'), ('NumBodies', 2)]), OrderedDict([('SystemName', 'BPM 17113'), ('NumBodies', 1)]), OrderedDict([('SystemName', 'Crucis Sector KN-T b3-4'), ('NumBodies', 1)]), OrderedDict([('SystemName', 'Hydrae Sector FM-V b2-4'), ('NumBodies', 3)]), OrderedDict([('SystemName', 'Shui Wei Sector XJ-Z b4'), ('NumBodies', 1)]), OrderedDict([('SystemName', 'Hyades Sector PN-J b9-4'), ('NumBodies', 1)]), OrderedDict([('SystemName', 'Igbo Kora'), ('NumBodies', 2)]), OrderedDict([('SystemName', 'Turots'), ('NumBodies', 13)]), OrderedDict([('SystemName', 'Miquich'), ('NumBodies', 1)]), OrderedDict([('SystemName', 'Paitina'), ('NumBodies', 5)]), OrderedDict([('SystemName', 'Rongites'), ('NumBodies', 6)]), OrderedDict([('SystemName', 'Col 285 Sector PH-B b14-5'), ('NumBodies', 1)]), OrderedDict([('SystemName', 'Carini'), ('NumBodies', 3)]), OrderedDict([('SystemName', 'ICZ DQ-X b1-6'), ('NumBodies', 1)]), OrderedDict([('SystemName', 'Col 285 Sector CK-X b15-6'), ('NumBodies', 1)]), OrderedDict([('SystemName', 'LFT 507'), ('NumBodies', 2)]), OrderedDict([('SystemName', 'Col 285 Sector IR-A b15-7'), ('NumBodies', 1)]), OrderedDict([('SystemName', 'Crucis Sector JS-T b3-8'), ('NumBodies', 2)]), OrderedDict([('SystemName', 'Graba'), ('NumBodies', 4)]), OrderedDict([('SystemName', 'Hyades Sector LZ-K a23-1'), ('NumBodies', 1)]), OrderedDict([('SystemName', 'Col 285 Sector SS-D a28-1'), ('NumBodies', 1)]), OrderedDict([('SystemName', 'LHS 253'), ('NumBodies', 1)]), OrderedDict([('SystemName', 'Puppis Sector AQ-P a5-2'), ('NumBodies', 1)]), OrderedDict([('SystemName', 'Trianguli Sector CB-N a7-2'), ('NumBodies', 1)]), OrderedDict([('SystemName', 'Col 285 Sector AA-A a30-5'), ('NumBodies', 1)])], 'BaseValue': 5454317, 'Bonus': 0, 'TotalEarnings': 5454317}
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


# TODO Refactor this...
def updateRowColorByBodyName(name, color):
    for frames in this.frame.winfo_children():
        frameName = str(frames).rpartition('.')[-1]
        if frameName == 'table_body':
            for bodyFrames in frames.winfo_children():
                bodyFrameName = str(bodyFrames).rpartition('.')[-1]
                if bodyFrameName == name.replace(' ', '-').lower():
                    for item in bodyFrames.winfo_children():
                        itemName = str(item).rpartition('.')[-1]
                        item.configure(fg=color)
