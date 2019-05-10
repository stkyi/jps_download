# runs $:python3.6 jps_download.py -y 2019 -m 4 -d 30
# downloads from gnss.geospace.ru .jps file
# converts file jps2rin_linux64 to .G .H .N .O
# copy .o to data/IGS/year/doy/
import argparse
import os
import threading
from ftplib import FTP
from datetime import datetime
import subprocess


class jps_download(FTP):
    def __init__(self, year, month, dom):
        super(jps_download, self).__init__()
        self.dom = self.hundred_format(dom)
        self.month = self.hundred_format(month)
        self.year = year

        self.url = 'gnss.geospace.ru'
        self.login = "external|caoUser"
        self.password = "caoipg2012"

        # path to download from
        self.path_download = "/DataAll/{0}/{1}/{2}/".format(self.year, self.month, self.dom)

        # path to save
        self.path_save = "/data/igs/DataAll/{0}/{1}/{2}/".format(self.year, self.month, self.dom)

        self.doy = self.doy_calc()
        self.path_to_IGS = "/data/IGS/{0}/{1}/".format(self.year, self.doy)
        # check if the path exists if not create
        self.createDir()

    def log_and_download(self):
        ftp = FTP(self.url)
        ftp.login(self.login, self.password)
        ftp.cwd(self.path_download)
        # ftp.retrlines('LIST')
        filelist = ftp.nlst()
        station_list = []
        threads = []
        for file, i in zip(filelist, range(len(filelist))):
            if not file[0:2] == "Z_" and file.endswith(".jps"):

                print("--------------------------{0} out of {1}".format(i, len(filelist)))
                if file[0:4] not in station_list:
                    print("station_list_add:" + str(file))
                    station_list.append(file[0:4])
                time = ftp.voidcmd("MDTM " + file)

                if self.find_file(file):
                    print(str(file) + ":" + str(time))
                    ftp.retrbinary("RETR " + file, open(self.path_save + str(file), 'wb').write)
                    th = threading.Thread(target=self.jps2rnx_cp(file))
                    th.start()
                    threads.append(th)
        ftp.quit()
        print("station_list:" + str(station_list))
        with open("{}".format(self.dom), "w") as file:
            for i in station_list:
                file.write(i + "\n")
        for thr in threads:
            thr.join()

    # checks given file if it is newer than 1 hour then download
    @staticmethod
    def find_file(filename):
        utc_now = datetime.utcnow()

        file_time = filename[5:-4]

        file_date = datetime(int(file_time[0:4]), int(file_time[5:7]), int(file_time[8:10]), int(file_time[11:13]),
                             int(file_time[14:16]), int(file_time[17:19]))

        if (utc_now - file_date).seconds < 3600:
            print("utc_now:" + str(utc_now))
            print("file_date:" + str(file_date))
            print(filename[5:-4])
            print((utc_now - file_date).seconds)
            print("download!")
            return True
        return False

    # check if the path exists if not create
    def createDir(self):

        if not os.path.exists(self.path_save):
            print("creating directory {0} ... ".format(self.path_save))
            try:
                # print("not os.path.exists(p):" + "inside try")
                bashCommand = "mkdir -p {0}".format(self.path_save)
                print("bashCommand:" + bashCommand)
                process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
                output, error = process.communicate()
                process.wait()
            # print("not os.path.exists(p):" + "inside try before except")
            except OSError as e:
                print(
                    "Creation of the directory {0} failed ".format(self.path_save) + " error:" + str(e))
                exit(1)
            else:
                print("Successfully created the directory {0} ".format(self.path_save))
        if not os.path.exists(self.path_to_IGS):
            print("creating directory {0} ... ".format(self.path_to_IGS))
            try:
                # print("not os.path.exists(p):" + "inside try")
                bashCommand = "mkdir -p {0}".format(self.path_to_IGS)
                print("bashCommand:" + bashCommand)
                process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
                output, error = process.communicate()
                process.wait()
            # print("not os.path.exists(p):" + "inside try before except")
            except OSError as e:
                print(
                    "Creation of the directory {0} failed ".format(self.path_to_IGS) + " error:" + str(e))
                exit(1)
            else:
                print("Successfully created the directory {0} ".format(self.path_to_IGS))

    # converts 3 to 03 etc
    @staticmethod
    def hundred_format(number):
        if int(number) < 10:
            return str("0" + str(int(number)))
        return number

    # converts saved .jps to .G .H .N .O
    def jps2rnx_cp(self, filename):
        file = filename[0:-4] + ".{0}o".format(str(self.year)[2:4])
        bashCommand = "chmod +x {0} && /data/igs/jps2rin_linux64 -o={1} {0}".format(
            self.path_save + str(filename),
            self.path_save)
        print("bashCommand:" + bashCommand)
        process = subprocess.Popen(bashCommand, stdout=subprocess.PIPE, shell=True)  # run bash command
        process.wait()  # wait until process ends
        self.cp(file)

    def cp(self, file):

        bashCommand = "cp {0} {1}".format(self.path_save + str(file), self.path_to_IGS + str(file[0:4] + str(self.doy))
                                          + ".{0}o".format(str(self.year)[2:4]))
        print("bashCommand:" + bashCommand)
        process = subprocess.Popen(bashCommand, stdout=subprocess.PIPE, shell=True)  # run bash command
        process.wait()  # wait until process ends

    def doy_calc(self):
        doy = datetime(int(self.year), int(self.month), int(self.dom)).timetuple().tm_yday
        return doy


if __name__ == "__main__":
    # Create object for parsing command-line options
    parser = argparse.ArgumentParser(description="Downloading .jps")
    # Add argument which takes path to a bag file as an input
    parser.add_argument("-d", "--day", type=str, help="add day", default="30")
    parser.add_argument("-m", "--month", type=str, help="add month", default="4")
    parser.add_argument("-y", "--year", type=str, help="add year", default="2019")
    args = parser.parse_args()
    jps = jps_download(args.year, args.month, args.day)
    jps.log_and_download()
