# DCP-Renamer is a program to rename Digital Cinema Packages
# It lives at https://github.com/ruhrmann/dcp-renamer
#
# runs with Python 2.7
#
#
#
# written by Peter Ruhrmann / ruhrmann(at)hdm-stuttgart.de
#
# License: GPL V3



from Tkinter import *
import tkFileDialog,tkMessageBox
import base64
import hashlib
import xml.etree.ElementTree as ET
import os

namespaces = {'cpl': 'http://www.smpte-ra.org/schemas/429-7/2006/CPL', 'pkl': 'http://www.smpte-ra.org/schemas/429-8/2007/PKL', 'am': 'http://www.smpte-ra.org/schemas/429-9/2007/AM', 'dsig': 'http://www.w3.org/2000/09/xmldsig#'}
ET.register_namespace('cpl', 'http://www.smpte-ra.org/schemas/429-7/2006/CPL') # needed to register the namespaces for CPL and PKL-files with multiple namespaces (e.g. signed files)
ET.register_namespace('pkl', 'http://www.smpte-ra.org/schemas/429-8/2007/PKL')
ET.register_namespace('am', 'http://www.smpte-ra.org/schemas/429-9/2007/AM')
ET.register_namespace('dsig', 'http://www.w3.org/2000/09/xmldsig#')


dirname = '.'
 
master = Tk()
master.title('DCP-Renamer')
master.minsize(300,180)
master.geometry('720x230')

 
def readDCP():
    global cplpath
    global pklpath
    global dirname # global to remember last used directory
    cplpath = '' # clear path if someone clicks "Read DCP"-Button a second time so that an exception will be thrown in writeCPL if no new DCP is loaded
    pklpath = '' # same as above
    comptitleentry.delete(0,END) # clear entry
    dirname = tkFileDialog.askdirectory(parent=master, initialdir=dirname, title='Choose DCP directory')
    if len(dirname ) > 0:
        pklfile = getPKL(dirname) # read ASSETMAP.xml and search for an asset-eynty with PackingList=='true'. Returns filename of PKL-File
        pklpath = dirname + '/' + pklfile 
        cplfile = getCPL(pklpath) # read PKL-File and search for an asset with type=='text/xml'. Returns filename of CPL-File
        cplpath = dirname + '/' + cplfile
        comptitle = getCompTitle(cplpath) # read CPL-File and get 'ContentTitleText'-Tag
        if comptitle != None: # if old DCP-Name is an empty String it should not crash
            comptitleentry.insert(0, comptitle)
        status.config(fg = 'blue', text='DCP loaded')
    return
        
def writeDCP():
    writeCPL(cplpath) # gets new Composition Title from comptitle entry, changes AnnotationText-Tag and ContentTitleText-Tag, and writes changed CPL-File
    cplchecksum = calcHash(cplpath) # calculates new hash for changed CPL-File
    writePKL(pklpath, cplchecksum) # write new hash to PKL-File and changes AnnotationText-Tag
    writeAM(dirname) # changes AnnotationText-Tag in ASSETMAP
    if checkRD.get() == 1: # rename the directory containing the DCP if checkbox is checked
        renameSourceDir(dirname)
    status.config(fg = 'dark green', text='DCP written')
    return
        

def getPKL(dirname):
    try:
        tree = ET.parse(dirname + '/ASSETMAP.xml')
    except IOError:
        status.config(fg = 'red', text='Directory does not contain a DCP. No ASSETMAP.xml found!')
        mainloop()
        
    root = tree.getroot()
    for assetlist in root.findall('am:AssetList',namespaces):
        for asset in assetlist.findall('am:Asset',namespaces):
                packinglist = asset.find('am:PackingList',namespaces)
                if packinglist != None:
                        if packinglist.text == 'true':
                                for chunklist in asset.findall('am:ChunkList',namespaces):
                                        for chunk in chunklist.findall('am:Chunk',namespaces):
                                                pklfile = chunk.find('am:Path',namespaces)
    return pklfile.text



def getCPL(path):
    tree = ET.parse(path)
    root = tree.getroot()
    for assetlist in root.findall('pkl:AssetList',namespaces):
        for asset in assetlist.findall('pkl:Asset',namespaces):
            filetype = asset.find('pkl:Type',namespaces)
            if filetype.text == 'text/xml':
                cplid = asset.find('pkl:Id',namespaces) # gets CPL Id. Using OriginalFileName-Tag does not work for DCPs from DCP-O-Matic
                # search the CPL Id in ASSETMAP.xml to get the CPL Path              
                tree = ET.parse(dirname + '/ASSETMAP.xml')
                root = tree.getroot()
                for assetlist in root.findall('am:AssetList',namespaces):
                    for asset in assetlist.findall('am:Asset',namespaces):
                        assetid = asset.find('am:Id',namespaces)
                        if assetid.text == cplid.text:
                            for chunklist in asset.findall('am:ChunkList',namespaces):
                                for chunk in chunklist.findall('am:Chunk',namespaces):
                                    cplfile = chunk.find('am:Path',namespaces)
                                    return cplfile.text
    return


def getCompTitle(path):
    tree = ET.parse(path)
    root = tree.getroot()
    comptitle = root.find('cpl:ContentTitleText',namespaces)
    return comptitle.text

def writeCPL(path):
    ET.register_namespace('', 'http://www.smpte-ra.org/schemas/429-7/2006/CPL') #default name space
    try:
        tree = ET.parse(path)
    except IOError:
        status.config(fg = 'red', text='Don\'t know what to write. You must load a DCP first!')
        mainloop()
        
    root = tree.getroot()
    comptitle = root.find('cpl:ContentTitleText',namespaces)
    comptitle.text = comptitleentry.get()
    annotext = root.find('cpl:AnnotationText',namespaces)
    annotext.text = comptitleentry.get()
    try:
        tree.write(path, encoding='utf-8', xml_declaration=True)
    except IOError:
        status.config(fg = 'red', text='Cannot write to disk. Do you have the permission to write the file?')
        mainloop()
    return

def calcHash(path):
    file = open(path, 'rb')
    if file != None:
        data = file.read()
        checksum = base64.b64encode(hashlib.sha1(data).digest())
        file.close()
        return checksum

def writePKL(path, checksum):
    ET.register_namespace('', 'http://www.smpte-ra.org/schemas/429-8/2007/PKL') #default name space
    tree = ET.parse(path)
    root = tree.getroot()
    annotext = root.find('pkl:AnnotationText',namespaces)
    annotext.text = comptitleentry.get()
    for assetlist in root.findall('pkl:AssetList',namespaces):
        for asset in assetlist.findall('pkl:Asset',namespaces):
            filetype = asset.find('pkl:Type',namespaces)
            if filetype.text == "text/xml":
                cplchecksum = asset.find('pkl:Hash',namespaces)
                cplchecksum.text = checksum
                annotext = asset.find('pkl:AnnotationText',namespaces)
                annotext.text = comptitleentry.get()
    tree.write(path, encoding='utf-8', xml_declaration=True)
    return

def writeAM(dirname):
    ET.register_namespace('', 'http://www.smpte-ra.org/schemas/429-7/2006/AM') #default name space
    try:
        tree = ET.parse(dirname + '/ASSETMAP.xml')
    except IOError:
        status.config(fg = 'red', text='Don\'t know what to write. You must load a DCP first!')
        mainloop()
        
    root = tree.getroot()
    annotext = root.find('am:AnnotationText',namespaces)
    annotext.text = comptitleentry.get()
    try:
        tree.write(dirname + '/ASSETMAP.xml', encoding='utf-8', xml_declaration=True)
    except IOError:
        status.config(fg = 'red', text='Cannot write to disk. Do you have the permission to write the file?')
        mainloop()
    return

def renameSourceDir(dirname):
    parent_path=os.path.dirname(dirname)
    os.rename(dirname,os.path.join(parent_path,comptitleentry.get()))
    return
    
# def createDCNC():
#    subwin = Toplevel()
#    subwin.title('Digital Cinema Naming Convetion Assistent')
#    subwin.geometry("640x480")
#    Label(subwin, justify=LEFT, text='Film Title:').place(x = 20, y = 20)
#    a = Entry(subwin, width = 20)
#    a.place(x = 80, y = 20)
#    x = Button(subwin, text='OK', command=sendDCNC(a.get()))
#    x.place(x = 20, y = 50)
#    return

#def sendDCNC(dcnc):
#    comptitleentry.delete(0,END)
#    comptitleentry.insert(0, dcnc)
    
    

 
readbutton = Button(master, text='Read DCP', command=readDCP)
readbutton.place(x = 20, y= 20)

Label(master, justify=LEFT, text='Composition Title:').place(x = 20, y = 50)

comptitleentry = Entry(master, width = 60)
comptitleentry.place(x = 150, y = 50)

# dcncbutton = Button(master, text='Create DCDN-Name', command=createDCNC)
# dcncbutton.place(x = 510, y = 46)

checkRD = IntVar(value=1)
checkrenamedir = Checkbutton(master, text="Rename directory containing the DCP", variable=checkRD)
checkrenamedir.place(x = 20, y= 80)

writebutton = Button(master, text='Write DCP', command=writeDCP)
writebutton.place(x = 20, y = 110)

status = Label(master)
status.place(x = 20, y = 140)

author = Label(master, justify=LEFT, text='Written by Peter Ruhrmann. If this program is useful for you, write me a mail: ruhrmann@hdm-stuttgart.de')
author.place(x = 20, y = 170)


mainloop()
