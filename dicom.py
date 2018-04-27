import wget
import os
import shutil
import os.path
import tarfile
import sys
import pydicom

def getfile(url,filename):
    retVal = False
    if os.path.exists(filename):
        if os.path.isfile(filename):
            os.remove(filename)
        else:
            shutil.rmtree(filename)
    try:
        wget.download(url,filename)
    except:
        print "Exception while trying to download from url "+url + "\n"
    if os.path.exists(filename):
        if os.path.isfile(filename):
            retVal = True
    return retVal

def extractfiles(tarfileName):
    tar = tarfile.open(tarfileName, 'r:gz')
    filesList = []
    for tarinfo in tar:
        filesList.append(tarinfo.name)
        tar.extract(tarinfo)
    tar.close()
    return filesList
    
def printExtraTags(dicomfile,ds):
    if (0x0008,0x0013) in ds and (0x0008,0x0032) in ds and (0x0020,0x0012) in ds and (0x0020,0x0013) in ds:
        print dicomfile + ": "+str(ds[0x0008,0x0013].value) +"\t"+ str(ds[0x0008,0x0032].value) + "\t" + str(ds[0x0020,0x0012].value) + "\t" + str(ds[0x0020,0x0013].value)
    else:
        print dicomfile +" does not have all tags\n"
    return

def parseTimeTag(tagValue):
    tagValue = float(tagValue)
    decPointPart = tagValue - int(tagValue)
    currentValue = int(tagValue)
    sec = currentValue%100
    currentValue = int(currentValue/100)
    min = currentValue%100
    hour = int(currentValue/100)
    return hour*3600+min*60+sec+decPointPart

if (len(sys.argv)==1):
    print "No Data file URL was provided\n"
    sys.exit(-1)
tarfileName = 'DataTar.tgz'
#url = 'https://s3.amazonaws.com/viz_data/DM_TH.tgz'
url = sys.argv[1]
if not getfile(url,tarfileName):
    print "Failed to get data file\n"
    sys.exit(-1)
files = extractfiles(tarfileName)
hospitals = []
names = []
patients = []
timeArr = {}
for dicomfile in files:
    ds = pydicom.dcmread(dicomfile)
    if  not os.path.exists(ds.PatientName):
        os.mkdir(ds.PatientName)
    nest = ds.PatientName + '/' + ds.StudyInstanceUID
    if not os.path.exists(nest):
        os.mkdir(nest)
    nest = ds.PatientName + '/' + ds.StudyInstanceUID + '/' + ds.SeriesInstanceUID
    if  not os.path.exists(nest):
        os.mkdir(nest)
    shutil.move(dicomfile,os.path.join(nest,dicomfile))
    if ds.InstitutionName not in hospitals:
        hospitals.append(ds.InstitutionName)
    if ds.PatientName not in names:
        names.append(ds.PatientName)
        patient = {'Name' : ds.PatientName,'Age' : ds.PatientAge,'Gender' : ds.PatientSex}
        patients.append(patient)
#    printExtraTags(dicomfile,ds)
    if (0x0008,0x0013) in ds and (0x0008,0x0031) in ds:
        seriesTime = parseTimeTag(ds[0x0008,0x0031].value)
        imageTime = parseTimeTag(ds[0x0008,0x0013].value)
        if ds.SeriesInstanceUID in timeArr:
            if imageTime > timeArr[ds.SeriesInstanceUID]['maxImage']:
                timeArr[ds.SeriesInstanceUID]['maxImage'] = imageTime
        else:
            firstInstance = {}
            firstInstance['series'] = seriesTime
            firstInstance['maxImage'] = imageTime
            timeArr[ds.SeriesInstanceUID] = firstInstance
print "Patients:\n"
pCount = 1
for patient in patients:
    print str(pCount)+") "+patient['Name']+ ". Age: " + patient['Age'] + ". Gender: " + patient['Gender'] + "\n"
    pCount+=1
print "\nNumber of hospitals: "+str(len(hospitals)) + "\n"
hosCount = 1;
for hos in hospitals:
    print str(hosCount)+") "+hos+"\n"
    hosCount+=1
seriesKeys = timeArr.keys()
for ser in seriesKeys:
	print "series "+ser+": difference between series time and latest image is "+str(timeArr[ser]['maxImage']-timeArr[ser]['series'])+" seconds\n"