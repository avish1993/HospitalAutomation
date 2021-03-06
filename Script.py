__author__ = 'obhi'
# Importing modules for reading CSV files, running the OS command CURL and writing to XML file
import csv
import sys
import os
import datetime
import logging
import glob  # For reading only *.csv files in the directory
import xml.etree.cElementTree as ET

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

handler = logging.FileHandler('update.log')
handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

hospitals = {
    'peerless': {'hosp_dets': {'dataSet': "C6ciemRdZvd", 'orgUnit': "o3Fdcxep773"},
                 'ITU': {'Total': "dToLU495hdD", 'Reserved': "WtlxTsYjvFO", 'Occupied': "HSSL9CQCEmu",
                         'Available': "rNdaHxXE13d"},
                 'ICCU': {'Total': "SRYSn6KiUgs", 'Reserved': "ix8dVgFAqbv", 'Occupied': "z5PMfjPOeaU",
                          'Available': "jW487vss0PK"},
                 'NICU': {'Total': "U97U38U2eBj", 'Reserved': "ys96ilizEcV", 'Occupied': "IAXlkWdrypq",
                          'Available': "MRCwMGNQOpg"},
                 },
    'bellevue': {'hosp_dets': {'dataSet': "L3NTA4t5LPS", 'orgUnit': "iNwzBcDqGsY"},
                 'CCU': {'Total': "G8RVMxO86Qc", 'Reserved': "GgULTaSUMBS", 'Occupied': "MhRIygQBvbx",
                         'Available': "brszB1hGZeG"},
                 'ITU': {'Total': "dToLU495hdD", 'Reserved': "WtlxTsYjvFO", 'Occupied': "HSSL9CQCEmu",
                         'Available': "rNdaHxXE13d"},
                 'ICCU': {'Total': "SRYSn6KiUgs", 'Reserved': "ix8dVgFAqbv", 'Occupied': "z5PMfjPOeaU",
                          'Available': "jW487vss0PK"},
                 'ICU-I': {'Total': "JXGDUZUxfC1", 'Reserved': "XJnDJzbnxIS", 'Occupied': "VEV5SQ3o4Cl",
                           'Available': "OJFT7dJ6UoL"},
                 'CTVS': {'Total': "B3zytjeLBkC", 'Reserved': "noOQUiGuYnC", 'Occupied': "dG9IYWemUNa",
                          'Available': "cZFZarClUkB"},
                 'NICU': {'Total': "U97U38U2eBj", 'Reserved': "ys96ilizEcV", 'Occupied': "IAXlkWdrypq",
                          'Available': "MRCwMGNQOpg"},
                 'SCBU': {'Total': "zDEFJIDCUjb", 'Reserved': "XqBI7j0SNWg", 'Occupied': "oF9zVVtGBz9",
                          'Available': "dCGFxlOVlwg"}
                 }
}


# Changing the directory to the directory where the CSV file is kept
# os.chdir('/home/obhi/Documents')

def indent(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def checkData(csvfile, hos_name):
    p = []
    for row in csvfile:
        if len(row) != 5:
            logger.info("Corrupt file. Either all fields not filled or excess data.")
            return False
        if row[0].upper() not in hospitals[hos_name]:
            logger.info("This type of bed doesnot exist for " + hos_name + "; bed_type = "+row[0])
            return False
        for r in row:
            if r == '':
                logger.info("File does not contain whole data, bed_type = " + row[0])
                return False
        try:
            int(row[1])
            int(row[2])
            int(row[3])
        except ValueError:
            logger.info("Bed count not in integer values, hosp name : " + hos_name + "; bed_type : " + row[0])
            return False
        if int(row[1]) < (int(row[2]) + int(row[3])):
            logger.info("Total beds less than Reserved and Occupied")
            return False
        if int(row[1]) < 0 or int(row[2]) < 0 or int(row[3]) < 0:
            logger.info("Bed count is negative")
            return False
        p.append(row[0].upper())
    b = list(set(p))
    p.sort()
    b.sort()
    if p != b:
        logger.info("Duplicates in bed_type")
        return False
    return True


def reader_writer_sender():
    bed_info = ['Total', 'Reserved', 'Occupied', 'Available']
    for filename in glob.glob('*.csv'):
        try:
            with open(filename, 'rb') as f:
                csvfile = csv.reader(f)
                if filename.lower()[:-4] in hospitals:
                    dataValueSet = ET.Element("dataValueSet")
                    dataValueSet.set("xmlns", "http://dhis2.org/schema/dxf/2.0")
                    hos_name = filename.lower()[:-4]
                    logger.info("Processing " + hos_name+ "; Started at "+str(datetime.datetime.now()))
                    dataValueSet.set("dataSet", hospitals[hos_name]['hosp_dets']['dataSet'])
                    dataValueSet.set("orgUnit", hospitals[hos_name]['hosp_dets']['orgUnit'])
                    with open(filename, 'rb') as fl:
                        if (checkData(csv.reader(fl), hos_name)):
                            for row in csvfile:
                                index = 1
                                bed_type = row[0].upper()
                                dataValueSet.set("completeDate", row[4])
                                dataValueSet.set("period", row[4][:8])
                                for b in bed_info:
                                    dataValue = ET.SubElement(dataValueSet, "dataValue")
                                    dataValue.set("dataElement", hospitals[hos_name][bed_type][b])
                                    if index == 4:
                                        dataValue.set("value", str(int(row[1]) - int(row[2]) - int(row[3])))
                                        break
                                    else:
                                        dataValue.set("value", row[index])
                                    index += 1
                            indent(dataValueSet)
                            tree = ET.ElementTree(dataValueSet)
                            xml_file_name = filename[:-4]
                            xml_file = xml_file_name + ".xml"
                            tree.write(xml_file, xml_declaration=True, encoding='utf-8', method="xml")
                            os.system("curl -d @" +xml_file+ " ""http://180.149.243.107:8080/api/dataValueSets"" -H ""Content-Type:application/xml"" -u admin:district -v")
                            logger.info("Successfully uploaded data of "+hos_name.upper()+" to server at " + str(datetime.datetime.now()))
                else:
                    logger.info("The filename sent by hospital is not valid : " + filename)
                    continue
        except:
            e = sys.exc_info()[0]
            logger.info("Error in reading files ::Message:: " + str(e))


if __name__ == '__main__':
    reader_writer_sender()
