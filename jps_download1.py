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
        self.path_save = "/srv/data/igs/DataAll/{0}/{1}/{2}/".format(self.year, self.month, self.dom)

        self.doy = self.doy_calc()
        print("dom:" + str(self.dom), "doy:" + str(self.doy))
        self.path_to_IGS = "/srv/data/IGS/{0}/{1}/".format(self.year, self.doy)
        self.path_to_igs = "/srv/data/igs/{0}/{1}/".format(self.year, self.doy)
        # check if the path exists if not create
        self.create_dir(self.path_save)
        self.create_dir(self.path_to_IGS)
        self.create_dir(self.path_to_igs)
        self.threads = []

    #главный метод, логинит на сайте и скачивает нужнгый файл
    def log_and_download(self):
        ftp = FTP(self.url)
        ftp.login(self.login, self.password)
        ftp.cwd(self.path_download)
        # ftp.retrlines('LIST')
        filelist = ftp.nlst()
        station_list = []

        for file, i in zip(filelist, range(len(filelist))):
            if not file[0:2] == "Z_" and file.endswith(".jps"):

                print("--------------------------{0} out of {1}".format(i, len(filelist)))
                if file[0:4] not in station_list:
                    self.create_dir(self.path_save + str(file[0:4]))
                    print("station_list_add:" + str(file))
                    station_list.append(file[0:4])
                time = ftp.voidcmd("MDTM " + file)
                if not self.find_file(file):
                    print(str(file) + ":" + str(time))

                    ftp.retrbinary("RETR " + file, open(self.path_save + str(file[0:4]) +"/"+ str(file), 'wb').write)


        ftp.quit()
        print("station_list:" + str(station_list))
        with open("{0}".format(self.path_save + str(self.dom)), "w") as file:
            for i in station_list:
                file.write(i + "\n")

    # converts 156 to 1560 etc
    @staticmethod
    def thousand_format(number):
        if int(number) < 1000:
            return str(str(int(number))+ "0")
        return str(number)

    def doy_calc(self):
        doy = datetime(int(self.year), int(self.month), int(self.dom)).timetuple().tm_yday
        return doy

    # checks if file name existed allready so you don`t need to download this again
    def find_file(self, filename):
        return False

    def create_dir(self,path):
        if not os.path.exists(path):
            print("creating directory {0} ... ".format(path))
            try:
                # print("not os.path.exists(p):" + "inside try")
                # вызывает bash linux что бы создать директорию
                bashCommand = "mkdir -p {0}".format(path)
                print("bashCommand:" + bashCommand)
                process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
                output, error = process.communicate()
                # ждет пока не создаст директорию
                process.wait()
            # print("not os.path.exists(p):" + "inside try before except")
            except OSError as e:
                print(
                    "Creation of the directory {0} failed ".format(path) + " error:" + str(e))
                exit(1)
            else:
                print("Successfully created the directory {0} ".format(path))

    # converts 3 to 03 etc
    @staticmethod
    def hundred_format(number):
        if int(number) < 10:
            return str("0" + str(int(number)))
        return number

    def iter_combine(self):
        print("iter_combine")
        for subdir, dirs, files in os.walk(self.path_save):
            for dir in dirs:
                print(dir)

                bashCommand = "cat {0}/*.jps >> {1}.jps".format(self.path_save + str(dir),
                                                                    self.path_save + str(dir) + "/" + str(dir))
                print("bashCommand:" + bashCommand)
                process = subprocess.Popen(bashCommand, stdout=subprocess.PIPE, shell=True)  # run bash command
                process.wait()  # wait until process ends
                th = threading.Thread(target=self.convert_relocate(self.path_save + str(dir) +"/"+ str(dir)+ ".jps"))
                th.start()
                self.threads.append(th)
        for thr in self.threads:
            thr.join()


    def convert_relocate(self,filename):
        # file = self.save_path + dir + / + mgmt1710.19
        file = filename[0:-4] + ".{0}".format(str(self.year)[2:4])
        print("file:" + str(file))
        self.jps2rnx(file[0:-3] + ".jps")
        self.obs_to_d(file + "o")
        self.zip(file + "d")

    # converts saved .jps to .G .H .N .O
    def jps2rnx(self, file):
        bashCommand = "chmod +x {0} && /srv/data/igs/jps2rin_linux64 -o={1} {0}".format(
            str(file),
            str(file)[:-13])
        print("bashCommand:" + bashCommand)
        process = subprocess.Popen(bashCommand, stdout=subprocess.PIPE, shell=True)  # run bash command
        process.wait()  # wait until process ends

    # converts .19o to .19d
    def obs_to_d(self,file):
        bashCommand = "rnx2crx {0} -f".format(self.path_save + file[-8:])
        print("bashCommand:" + bashCommand)
        process = subprocess.Popen(bashCommand, stdout=subprocess.PIPE, shell=True)  # run bash command
        process.wait()  # wait until process ends

    # zip file to .19d.Z
    def zip(self,file):
        print(str(file)+ ", " + str(file[-8:-4]) + ", " + str(file[-4:]))
        bashCommand = "compress -f {0} && cp {1} {2}".format(self.path_save + file[-8:],self.path_save + file[-8:] + ".Z", self.path_to_igs + str(file)[-8:-4] + str(self.thousand_format(self.doy)) + str(file)[-4:] +".Z")
        print("bashCommand:" + bashCommand)
        process = subprocess.Popen(bashCommand, stdout=subprocess.PIPE, shell=True)  # run bash command
        process.wait()  # wait until process ends




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
    jps.iter_combine()
    print("end")
