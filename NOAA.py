import logging
logging.basicConfig(level=logging.DEBUG, format=" %(asctime)s - %(levelname)s - %(message)s")
logging.debug("Start of program")
import gzip
import os
import urllib2
from StringIO import StringIO
import csv
import re
from tkMessageBox import showerror, showinfo, showwarning
from tkinter import Tk, Label, Entry, Button,OptionMenu, Frame, TOP, LEFT, IntVar, StringVar
from datetime import datetime
from matplotlib.dates import DateFormatter, MonthLocator, date2num, num2date
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, RadioButtons, Cursor, MultiCursor
import numpy as np

BASEPATH = "ftp://ftp.ncdc.noaa.gov/pub/data/noaa/isd-lite/"
DEVICEPATH = "ftp://ftp.ncdc.noaa.gov/pub/data/noaa/isd-history.csv"
LEGENDPATH = "ftp://ftp.ncdc.noaa.gov/pub/data/noaa/isd-lite/isd-lite-format.txt"


# TODO add urlopen not reachable exception handler

class Demo():
    def __init__(self):
        self.root = Tk()
        self.root.title("NOAA")
        self.fetchYear()
        self.fetchDevice()
        self.fetchInterpreter()
        self.panelize()
        # self.root.config(menu=self.menubar)
        self.root.mainloop()

    def panelize(self):
        # ========================================1st Frame=============================================================
        self.yearFrame = Frame(self.root)
        self.yearFrame.pack(side=TOP, fill= "both", expand=1, pady=10, padx=10)
        Label(self.yearFrame,text="year:\t", font=("Arial", 16, "bold")).pack(side=LEFT, fill="both")

        self.startYearVar = IntVar()
        self.startYearEntry = Entry(self.yearFrame, textvariable=self.startYearVar)
        self.startYearVar.set(self.yearList[0])
        self.startYearEntry.pack(side=LEFT, fill="both")

        Label(self.yearFrame, text="to", font=("Arial", 16, "bold")).pack(side=LEFT, fill="both")

        self.endYearVar = IntVar()
        self.endYearEntry = Entry(self.yearFrame, textvariable=self.endYearVar)
        self.endYearVar.set(1910)
        self.endYearEntry.pack(side=LEFT, fill="both")
        # =========================================2nd Frame============================================================
        self.deviceFrame = Frame(self.root)
        self.deviceFrame.pack(side=TOP, fill="both",expand=1, pady=10, padx=10)
        Label(self.deviceFrame, text="USAF#:\t", font=("Arial",16,"bold")).pack(side=LEFT, fill="both")

        self.deviceVar = StringVar()
        self.deviceEntry = Entry(self.deviceFrame, textvariable=self.deviceVar)
        self.deviceVar.set("029070")
        self.deviceEntry.pack(side=LEFT, fill="both")
        # ==========================================No Frame============================================================
        self.confirmBut = Button(self.root, text="Confirm", font=("Arial", 16 ,"bold"), command=self.execute, pady=10, padx=10)
        self.confirmBut.pack(side=TOP, expand=1)

    def execute(self):
        # TODO optimize check-if-exist algorithm by directly accessing via urlopen and verifying .gz file path existance
        self.datalogPath = os.getcwd() + "//dataLog.csv"
        # Check if already exist. If exists, delete existing file first and then proceed with create a blank file
        if os.path.exists(self.datalogPath):
            os.remove(self.datalogPath)
        open(self.datalogPath, "w").close()
        # Check if startYear and endYear fall within range of yearList
        logging.debug("not done")
        if not self.startYearVar.get() >= min(self.yearList) or not self.endYearVar.get() <= max(self.yearList):
            showerror("Error","Year NOT within range, stopping...")
            return (False)
        else:
            # Re-order startYear and endYear from small to large if not in order
            if not self.startYearVar.get() <= self.endYearVar.get():
                endYear, startYear = self.startYearVar.get(), self.endYearVar.get()
                self.startYearVar.set(startYear)
                self.endYearVar.set(endYear)

        yearRange = [year for year in self.yearList if year >= self.startYearVar.get() and year <= self.endYearVar.get()]
        for year in [str(x) for x in yearRange]:

            logging.info("processing %s of year %s" % (self.deviceVar.get(), year))

            # path of folder denoted by years
            path = BASEPATH+year+"/"
            request = urllib2.urlopen(urllib2.Request(path))
            fileList = [y.split(" ")[-1] for y in [x for x in request.read().split("\n") if x ]]
            request.close()
            if any([self.deviceVar.get() in filename.split("-")[0] for filename in fileList]):
                # Assuming there's Max one matched file exist for given year
                request = urllib2.Request(BASEPATH+year+"/"+[filename for filename in fileList if self.deviceVar.get() in filename][0])
                request.add_header('Accept-encoding', 'gzip')
                response = urllib2.urlopen(request)
                temp = StringIO(response.read())
                response.close()
                fIn = gzip.GzipFile(fileobj=temp)
                data = [x for x in fIn.read().split("\n") if x ]
                # Record data to temp file to clear off memories
                with open(self.datalogPath, "a") as csvfile:
                    names = [posDict["Name"] for posDict in self.posDictList]
                    writer = csv.DictWriter(csvfile, fieldnames=names, lineterminator="\n")
                    writer.writeheader()

                    for lineIn in data:
                        lineOut = [x for x in lineIn.split(" ") if x ]
                        try:
                            writer.writerow(dict([(key, lineOut[index]) for index, key in enumerate(names)]))
                        except IndexError:
                            logging.error("Error","Error occurs, debug here")
                        else:
                            pass

        self.plot()


    def plot(self):
        STYLES = ['#a9a9a9', '#222222', '#f3c300', '#875692', '#f38400', '#a1caf1', '#be0032', '#c2b280',
                  '#848482',
                  '#008856', '#e68fac', '#0067a5', '#f99379', '#604e97', '#f6a600', '#b3446c', '#dcd300',
                  '#882d17',
                  '#8db600', '#654522', '#e25822', '#2b3d26']
        # Plot data points with data stored in dataLog.csv
        with open(self.datalogPath, "rU") as csvfile:
            reader = csv.DictReader(csvfile)
            content = [row for row in reader]
            X, Y = [], []
            timeVarList = ["Observation Year", "Observation Month", "Observation Day", "Observation Hour"]
            for index,datapoint in enumerate(content):
                try:
                    X.append(datetime.strptime("-".join([datapoint[x] for x in timeVarList]), "%Y-%m-%d-%H"))
                except ValueError:
                    logging.warning("Corrupted X data point found, skipping...")
                else:
                    pass
            dataNameList = [key for key in content[0].keys() if not any([name in key for name in timeVarList])]
            # Set up plot properties
            months = MonthLocator()
            monthsFmt = DateFormatter("%Y-%m-%d-%H")
            axrowNum = 2
            if len(dataNameList) % axrowNum != 0:
                axcolNum = len(dataNameList) / axrowNum + 1
            elif len(dataNameList) % axrowNum == 0:
                axcolNum = len(dataNameList) / axrowNum
            self.fig, self.axarr = plt.subplots(axrowNum, axcolNum, sharex=True)
            # Start plotting for each data type
            for i, dataName in enumerate(dataNameList):
                Y= []
                for y in content:
                    try:
                        float(y[dataName])
                    except ValueError:
                        logging.warning("Corrupted Y data point found, skipping...")
                    else:
                        # Fetch MISSING VALUE and SCALING FACTOR and apply to Y data points accordingly
                        mvList = [int(dict["MISSING VALUE"]) for dict in self.posDictList if dataName in dict["Name"] and "MISSING VALUE" in dict.keys()]
                        scaleList = [int(dict["SCALING FACTOR"]) for dict in self.posDictList if dataName in dict["Name"] and "SCALING FACTOR" in dict.keys()]
                        Y.append(int(y[dataName])*(scaleList[0] if scaleList else 1) if not int(y[dataName]) == (mvList[0] if mvList else None) else None)
                axcol, axrow = i / axrowNum, i % axrowNum
                X = np.array(X)
                Y = np.array(Y).astype(np.double)
                Ymask = np.isfinite(Y)
                # use Ymask to filter out None value in Y and map to X and Y for plots
                self.axarr[axrow, axcol].plot(X[Ymask], Y[Ymask], linestyle='--', markersize=1, marker='o',color=STYLES[i],label=dataName)
                handles, labels = self.axarr[axrow, axcol].get_legend_handles_labels()
                self.axarr[axrow, axcol].legend(handles[::-1], labels[::-1])
                # decorations
                self.axarr[axrow, axcol].ticklabel_format(style='sci', scilimits=(-3, 4), axis='y')
                self.axarr[axrow, axcol].set_xlabel('time', fontsize=8)
                # turn off interaction mode to turn to use multiCursor
                # axarrList = [item for sublist in self.axarr.tolist() for item in sublist]
                # multiCursor = MultiCursor(self.fig.canvas, (axarrList), vertOn=True, color='k', lw=1)
                self.fig.canvas.set_window_title('device %s data from %s to %s ' % (self.deviceVar.get(),self.startYearVar.get(), self.endYearVar.get()))
                # turn on interaction mode for adding subplots to canvas in multiple re-entrys
                plt.ion()
                plt.show()
                plt.pause(0.01)

    def fetchYear(self):
        # Fetch list of available folder options denoted by year from NOAA repository and list of available years in "yearList"
        request = urllib2.urlopen(urllib2.Request(BASEPATH))
        detailList = request.read().split("\n")
        yearList = [elm.split(" ")[-1] for elm in detailList if elm.split(" ")[-1]]
        for i, x in enumerate(yearList):
            try:
                float(x)
            except ValueError:
                yearList[i] = ""
            else:
                pass
        self.yearList = [int(x.strip()) for x in yearList if x]
        request.close()

    def fetchDevice(self):
        # Fetch station data as csv and store in "devicesDict"
        request = urllib2.urlopen(DEVICEPATH)
        fIn = csv.DictReader(request)
        self.deviceDict = [line for line in fIn]
        request.close()

    def fetchInterpreter(self):
        # Fetch and filter out legends and store as "self.posDictList"
        request = urllib2.urlopen(LEGENDPATH)
        context = request.read()
        self.posDictList = []
        for field in re.split("Field.*?:", context):
            posDict = {}
            pattern = re.compile(
                r"Pos\s?(\d+)-(\d+).*?Length\s?\d+:\s?(.*?)\n.*\n?(UNITS:.*?\n)?(SCALING FACTOR:.*?\n)?(MISSING VALUE:.*?\n)?(DOMAIN:.*?\n)?\n?")
            if re.search(pattern, field):
                listOut = [x for x in re.findall(pattern, field)[0] if x]
                listOut = [x + (field.split("DOMAIN:\n")[-1] if "DOMAIN" in x else "") for x in listOut]
                for i, key in enumerate(["Start Pos", "End Pos", "Name"]):
                    posDict[key] = listOut[i]
                if len(listOut) > len(["Start Pos", "End Pos", "Name"]):
                    for i in range(len(["Start Pos", "End Pos", "Name"]) + 1, len(listOut)):
                        if not len(listOut[i].strip().split("\n")) > 1:
                            key, value = listOut[i].strip().split(":")
                            posDict[key] = value
                            # Assuming at most one hierachical structure here -- ie, {Doman: {1,2,3}} rather than {Domain: {1: {A,B,C}}, {2: {D,E}}, {3: {F,G}}}
                        else:
                            posDict[listOut[i].split("\n")[0].split(":")[0]] = [x for x in listOut[i].split("\n")[1:] if
                                                                                x]
                self.posDictList.append(posDict)
        request.close()


if __name__ == "__main__":
    Demo()