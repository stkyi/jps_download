# run $:python3.6 jps_download.py -y 2019 -m 4 -d 30
# downloads from gnss.geospace.ru .jps files
# converts files jps2rin_linux64 to .G .H .N .O
# converts .19o to .19d.Z
# sends .19d.Z to /data/igs/YEAR/DOM/
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
        # адресс откуда скачиваем и пароль
        self.url = 'gnss.geospace.ru'
        self.login = "external|caoUser"
        self.password = "caoipg2012"

        # path to download from (website)
        self.path_download = "/DataAll/{0}/{1}/{2}/".format(self.year, self.month, self.dom)

        # path to save
        self.path_save = "/data/igs/DataAll/{0}/{1}/{2}/".format(self.year, self.month, self.dom)

        self.doy = self.doy_calc()
        print("doy:" + str(self.doy))
        self.path_to_IGS = "/data/IGS/{0}/{1}/".format(self.year, self.doy)
        self.path_to_igs = "/data/igs/{0}/{1}/".format(self.year, self.doy)
        # check if the path exists if not create
        self.createDir()

#главный метод, логинит на сайте и скачивает нужнгый файл
    def log_and_download(self):
        ftp = FTP(self.url)
        ftp.login(self.login, self.password)
        ftp.cwd(self.path_download)
        # ftp.retrlines('LIST')
        filelist = ftp.nlst()
        station_list = []
        self.path_save + str(file[0:4]) +"/"+ str(file),
        for file, i in zip(filelist, range(len(filelist))):
            if not file[0:2] == "Z_" and file.endswith(".jps"):

                print("--------------------------{0} out of {1}".format(i, len(filelist)))
                if file[0:4] not in station_list:
                    print("station_list_add:" + str(file))
                    station_list.append(file[0:4])
                time = ftp.voidcmd("MDTM " + file)

                print(str(file) + ":" + str(time))
                ftp.retrbinary("RETR " + file, open(self.path_save +"{0}/".format(file[0:4])+ str(file), 'wb').write)
                #with open("saved_obs_{0}".format(self.doy), "w") as file_read:
                #   file.write(file)
                # th = threading.Thread(target=self.convert_relocate(file))
                # th.start()
                # threads.append(th)
        ftp.quit()
        print("station_list:" + str(station_list))
        with open("{0}".format(self.dom), "w") as file:
            for i in station_list:
                file.write(i + "\n")

        self.iter_combine()
        for thr in self.threads:
            thr.join()
    # обьединяем все файлы и отправляем их conv_relocate
    def iter_combine(self):
        for subdir, dirs, files in os.walk(self.path_save):
            for dir in dirs:
                print(dir)
                bashCommand = "copy *.jps /b {0}.jps /b".format(dir + self.thousand_format(self.doy))
                print("bashCommand:" + bashCommand)
                process = subprocess.Popen(bashCommand, stdout=subprocess.PIPE, shell=True)  # run bash command
                process.wait()  # wait until process ends
                th = threading.Thread(target=self.convert_relocate(dir + self.thousand_format(self.doy)))
                th.start()
                self.threads.append(th)

    # checks if file name existed allready so you don`t need to download this again
    def find_file(self, filename):
        with open("saved_obs_{0}".format(self.doy),"r") as file_read:
            loglist = file_read.readlines()
            for line in loglist:
                if str(filename) in line:
                    return True


        """
        # checks given file if it is newer than 1 hour then download
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
            return True"""
        return False

    # check if the path exists if not create
    def createDir(self):
        # создаем директорию для скачанных файлов с сайта
        if not os.path.exists(self.path_save):
            print("creating directory {0} ... ".format(self.path_save))
            try:
                # print("not os.path.exists(p):" + "inside try")
                #вызывает bash linux что бы создать директорию
                bashCommand = "mkdir -p {0}".format(self.path_save)
                print("bashCommand:" + bashCommand)
                process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
                output, error = process.communicate()
                #ждет пока не создаст директорию
                process.wait()
            # print("not os.path.exists(p):" + "inside try before except")
            except OSError as e:
                print(
                    "Creation of the directory {0} failed ".format(self.path_save) + " error:" + str(e))
                exit(1)
            else:
                print("Successfully created the directory {0} ".format(self.path_save))
        # создаем директорию для файлов наблюдений
        if not os.path.exists(self.path_to_IGS):
            print("creating directory {0} ... ".format(self.path_to_IGS))
            try:
                # print("not os.path.exists(p):" + "inside try")\
                # вызывает bash linux что бы создать директорию
                bashCommand = "mkdir -p {0}".format(self.path_to_IGS)
                print("bashCommand:" + bashCommand)
                process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
                output, error = process.communicate()
                # ждет пока не создаст директорию
                process.wait()
            # print("not os.path.exists(p):" + "inside try before except")
            except OSError as e:
                print(
                    "Creation of the directory {0} failed ".format(self.path_to_IGS) + " error:" + str(e))
                exit(1)
            else:
                print("Successfully created the directory {0} ".format(self.path_to_IGS))

        if not os.path.exists(self.path_to_igs):
            print("creating directory {0} ... ".format(self.path_to_igs))
            try:
                # print("not os.path.exists(p):" + "inside try")\
                # вызывает bash linux что бы создать директорию
                bashCommand = "mkdir -p {0}".format(self.path_to_igs)
                print("bashCommand:" + bashCommand)
                process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
                output, error = process.communicate()
                # ждет пока не создаст директорию
                process.wait()
            # print("not os.path.exists(p):" + "inside try before except")
            except OSError as e:
                print(
                    "Creation of the directory {0} failed ".format(self.path_to_igs) + " error:" + str(e))
                exit(1)
            else:
                print("Successfully created the directory {0} ".format(self.path_to_igs))

    # converts 3 to 03 etc
    @staticmethod
    def hundred_format(number):
        if int(number) < 10:
            return str("0" + str(int(number)))
        return number
    # converts 156 to 1560 etc
    @staticmethod
    def thousand_format(number):
        if int(number) < 1000:
            return str(str(int(number))+ "0")
        return str(number)
    def convert_relocate(self,filename):
        # file = mgmt1710.19
        file = filename[0:-4] + ".{0}".format(str(self.year)[2:4])

        self.jps2rnx(file[0:-3] + ".jps")
        self.obs_to_d(file + "o")
        self.zip(file + "d")


    # converts saved .jps to .G .H .N .O
    def jps2rnx(self, file):
        bashCommand = "chmod +x {0} && /data/igs/jps2rin_linux64 -o={1} {0}".format(
            self.path_save +"{0}/".format(file[0:4]) + str(file),
            self.path_save)
        print("bashCommand:" + bashCommand)
        process = subprocess.Popen(bashCommand, stdout=subprocess.PIPE, shell=True)  # run bash command
        process.wait()  # wait until process ends

    # converts .19o to .19d
    def obs_to_d(self,file):
        bashCommand = "rnx2crx {0} -f".format(self.path_save +"{0}/".format(file[0:4])+ str(file))
        print("bashCommand:" + bashCommand)
        process = subprocess.Popen(bashCommand, stdout=subprocess.PIPE, shell=True)  # run bash command
        process.wait()  # wait until process ends

    # zip file to .19d.Z
    def zip(self,file):
        bashCommand = "compress -f {0} && cp {1} {2}".format(self.path_save +"{0}/".format(file[0:4])+ str(file),self.path_save + str(file) + ".Z", self.path_to_igs + str(file)[:4] + str(self.doy) + str(file)[-4:] +".Z")
        print("bashCommand:" + bashCommand)
        process = subprocess.Popen(bashCommand, stdout=subprocess.PIPE, shell=True)  # run bash command
        process.wait()  # wait until process ends

    """def cp(self,file1,file2):
        bashCommand = "cp {0} {1}".format(file1,file2)
        print("bashCommand:" + bashCommand)
        process = subprocess.Popen(bashCommand, stdout=subprocess.PIPE, shell=True)  # run bash command
        process.wait()  # wait until process ends 
        """

    """"def cp_to_IGS(self, file):

        bashCommand = "cp {0} {1}".format(self.path_save + str(file), self.path_to_IGS + str(file[0:4] + str(self.doy))
                                          + ".{0}o".format(str(self.year)[2:4]))
        print("bashCommand:" + bashCommand)
        process = subprocess.Popen(bashCommand, stdout=subprocess.PIPE, shell=True)  # run bash command
        process.wait()  # wait until process ends"""

    def doy_calc(self):
        doy = datetime(int(self.year), int(self.month), int(self.dom)).timetuple().tm_yday
        return doy


if __name__ == "__main__":
    # Create object for parsing command-line options
    parser = argparse.ArgumentParser(description="Downloading .jps")
    # Add argument which takes path to a file as an input
    parser.add_argument("-d", "--day", type=str, help="add day", default="30")
    parser.add_argument("-m", "--month", type=str, help="add month", default="4")
    parser.add_argument("-y", "--year", type=str, help="add year", default="2019")
    args = parser.parse_args()
    jps = jps_download(args.year, args.month, args.day)
    jps.log_and_download()
