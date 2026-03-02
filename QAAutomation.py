import argparse
import pandas as pd
import pymongo
import csv
import os
from datetime import datetime
from pprint import pprint

def normalize(row):
    return " ".join(str(row).strip().lower().split())

def checkEmpty():
    if fallCollection.count_documents({}) == 0 or springCollection.count_documents({}) == 0:
        parser.error("Databases must be filled")

def dupeChecker(fallQuery,springQuery):
    csvList = []
    testCases = set()
    
    #Fall DB
    for row in fallQuery:
        #Checks if current row is valid entry
        if not validChecker(row):
            continue
        #Takes current rows, Columns to put in a set to compare duplicates
        key = (
            normalize(row.get("Build #", "")),
            normalize(row.get("Category", "")) ,
            normalize(row.get("Test Case", "")) ,
            normalize(row.get("Expected Result", "")),
            normalize(row.get("Actual Result", ""))
        )

        #Checks if row already exists in set
        if key in testCases:
            continue
        
        #read each row and add it to the set to compare to other db
        testCases.add(key)
        #Add each row to final list
        csvList.append(row)

    #Spring DB
    for row in springQuery:
        if not validChecker(row):
            continue
        
        key = (
            normalize(row.get("Build #", "")),
            normalize(row.get("Category", "")) ,
            normalize(row.get("Test Case", "")) ,
            normalize(row.get("Expected Result", "")),
            normalize(row.get("Actual Result", ""))
        )
        #Adds All Rows of Fall Sheet into testCases to compare for duplicates
        
        if key not in testCases:
            csvList.append(row)
            testCases.add(key)

    return csvList

def validChecker(row):
    #Checks if NAN, None, Empty for all columns
    if (pd.isna(row['Test #'])
        or pd.isna(row['Build #'])
        or pd.isna(row['Category'])
        or pd.isna(row['Expected Result']) 
        or pd.isna(row['Actual Result']) 
        or pd.isna(row['Test Case'])
        or pd.isna(row['Repeatable?'])
        or pd.isna(row['Blocker?'])
        or pd.isna(row['Test Owner'])
        or not row['Test #']
        or not row['Build #']
        or not row['Category']
        or not row['Expected Result']
        or not row['Actual Result']
        or not row['Test Case']
        or not row['Repeatable?']
        or not row['Blocker?']
        or not row['Test Owner']
    ):
        return False
    
    try:
        #Checks if Test # is an int
        int(row['Test #'])

        #Checks if its a valid date
        datetime.strptime(row['Build #'], "%Y-%m-%d %H:%M:%S")

        #Checks if Category is a string
        str(row['Category'])

    #Error Handling
    except (ValueError, TypeError):
        #If Error Skip entry
        return False
    
    #Checks Repeatable if yes, no, y, n
    if normalize(row.get('Repeatable?')) not in ["yes","y","n","no"]:
        return False
    
    if normalize(row.get('Blocker?')) not in ["yes","y","n","no"]:
        return False
    
    return True

#Connect MongoDB
myClient = pymongo.MongoClient("mongodb://localhost:27017/")

#Makes DB
db = myClient["GameReviews"]
fallCollection = db["Fall2025"]
springCollection = db["Spring2025"]
encodings = ['utf-8','latin-1']

#Fill Database grouping
parser = argparse.ArgumentParser(description='Combine Two Data and reveal the rats')

parser.add_argument('--verbose', action='store_true',dest='verbose', help='Tells the program you want more detailed view')


fillDB = parser.add_argument_group("Fills Database using argument --fill")

fillDB.add_argument('--fill',type=str,choices=['databases'] ,dest='fill')

fillDB.add_argument('file1',nargs='?',metavar='FILE', type = str,
                    help='First XLSX file path')

fillDB.add_argument('file2',nargs='?',metavar='FILE', type = str,
                    help='Second XLSX file path')

parser.add_argument('--user',type=str,metavar=': "name"', help="Input User to find all records", dest='user')

parser.add_argument('--repeatable', action='store_true', help="Outputs all Repetable", dest="repeat")

parser.add_argument('--blocker', action='store_true', help="Outputs all Blocker",dest="blocker")

parser.add_argument('--date', type=str, help="Outputs Users of a specific date", dest="date")

args = parser.parse_args()

#If verbose isn't used
if args.verbose:

    #Fills the database for this option
    if args.fill == 'databases':
        #DB Fill Logic
        #If no files are submitted with fill
        if args.fill and (not args.file1 or not args.file2):
            parser.error("--fill requires two Excel file arguments (FILE FILE)")

        file1 = args.file1
        file2 = args.file2

        fallExcel = None
        springExcel = None

        #Puts Fall and Spring in respective Collections
        for f in [file1, file2]:
            name = f.lower()
            if "fall" in name:
                fallExcel = f
            elif "spring" in name:
                springExcel = f

        #If one of the files isn't detected
        if not fallExcel:
            parser.error("Couldn't detect 'Fall'")

        if not springExcel:
            parser.error("Couldn't detect 'Spring'")

        #Create Temp CSV Files for each xlsx
        fallTempCSV = "tempFall.csv"
        springTempCSV = "tempSpring.csv"

        #Read XLSX files and convert to csv
        #Fall
        df = pd.read_excel(fallExcel)
        df.to_csv(fallTempCSV, index=False)

        #Spring
        df = pd.read_excel(springExcel)
        df.to_csv(springTempCSV, index=False)

            
        #Reading CSV writing to DB
        
        # Fall 2025
        for encoding in encodings:
            try:
                df = pd.read_csv(fallTempCSV, encoding=encoding)
                reviews = df.to_dict(orient='records')
                fallCollection.delete_many({})
                fallCollection.insert_many(reviews)

            except UnicodeDecodeError:
                print("Encoding Error")

        for encoding in encodings:
            # Spring2025
            try:
                df = pd.read_csv(springTempCSV, encoding=encoding)
                reviews = df.to_dict(orient='records')
                springCollection.delete_many({})
                springCollection.insert_many(reviews)

            except UnicodeDecodeError:
                print("Encoding Error")
        
        #Removes CSV files
        os.remove(fallTempCSV)
        os.remove(springTempCSV)

    if args.fill == "csvOutput":
        print("Give Good CSV Output")

#REPEAT AND BLOCKER ARG
    if args.repeat and args.blocker:
        checkEmpty()

        # #Depending on whatever the user says that becomes the query with associated list checking both
        # if repeatUsers.lower() == "yes" or repeatUsers.lower() == "y":
        #     repeat = "^(yes|y)$"
            

        # elif repeatUsers.lower() == "no" or repeatUsers.lower() == "n":
        #     repeat = "^(no|n)$"
            

        # if blockerUser.lower() == "yes" or blockerUser.lower() == "y":
        #     blocker = "^(yes|y)$"
            

        # elif blockerUser.lower() == "no" or blockerUser.lower() == "n":
        #     blocker = "^(no|n)$"

            

        #Fetch rows both Repeatable? and Blocker? = yes/y
        both = {
            "$and": [
                {'Blocker?': {"$regex": "^(yes|y)$", "$options": "i"}},
                {'Repeatable?': {"$regex": "^(yes|y)$", "$options": "i"}}
            ]
        }
        fallQuery = list(fallCollection.find(both))
        springQuery = list(springCollection.find(both))
        keys = fallQuery[0].keys()
        
        csvList = dupeChecker(fallQuery,springQuery)
        
        with open("repeatable&blocker.csv",'w', newline='', encoding="utf-8") as output:
            writer = csv.DictWriter(output, fieldnames=keys)
            writer.writeheader()
            writer.writerows(csvList)
        pprint(csvList)

#REPEAT ARG
    if args.repeat:
        #Checks If Database is initialized
        checkEmpty()

        # Initally had it checking for user input
        # if repeatUsers.lower() == "yes" or repeatUsers.lower() == "y":
        #     repeat = "^(yes|y)$"

        # elif repeatUsers.lower() == "no" or repeatUsers.lower() == "n":
        #     repeat = "^(no|n)$"
        # else:
        #     parser.error("Invalid argument for --repeat (use yes/y or no/n)")

        #^ = Start of String   $ = End of String    $regex = pattern recognition  $options: Ignore Case sensitivity
        yes = {'Repeatable?': {"$regex": "^(yes|y)$", "$options": "i"}}
        yesFallQuery = list(fallCollection.find(yes))
        yesSpringQuery = list(springCollection.find(yes))
        keys = yesFallQuery[0].keys()
        
        csvList = dupeChecker(yesFallQuery,yesSpringQuery)
        
        with open("repeatable.csv",'w', newline='', encoding="utf-8") as output:
            writer = csv.DictWriter(output, fieldnames=keys)
            writer.writeheader()
            writer.writerows(csvList)
        pprint(csvList)
            
        
    if args.blocker:
        # Initally had it checking for user input
        # if blockerUser.lower() == "yes" or blockerUser.lower() == "y":
        #     blocker = "^(yes|y)$"
            
        # elif blockerUser.lower() == "no" or blockerUser.lower() == "n":
        #     blocker = "^(no|n)$"
        # else:
        #     parser.error("Invalid argument for --blocker (use yes/y or no/n)")

        checkEmpty()
        #^ = Start of String   $ = End of String    $regex = pattern recognition  $options: Ignore Case sensitivity
        blocker = {'Blocker?': {"$regex": "^(yes|y)$", "$options": "i"}}
        yesFallQuery = list(fallCollection.find(blocker))
        yesSpringQuery = list(springCollection.find(blocker))
        keys = yesFallQuery[0].keys()
        
        csvList = dupeChecker(yesFallQuery,yesSpringQuery)
        
        with open("blocker.csv",'w', newline='', encoding="utf-8") as output:
            writer = csv.DictWriter(output, fieldnames=keys)
            writer.writeheader()
            writer.writerows(csvList)
        pprint(csvList)

#USER ARG

    if args.user:
        #If Database hasn't been initialized yet
        checkEmpty()
        
        searchUser = args.user
        myquery = {'Test Owner': {"$regex": f"^{searchUser}$", "$options": "i"}}
        fallQuery = list(fallCollection.find(myquery))
        springQuery = list(springCollection.find(myquery))
        #Get Current Keys of CSV
        keys = fallQuery[0].keys()

        csvList = dupeChecker(fallQuery,springQuery)
        
        #Writer
        with open("kevinChaja.csv",'w',encoding="utf-8" ,newline='') as output:
            writer = csv.DictWriter(output, fieldnames=keys)
            writer.writeheader()
            writer.writerows(csvList)

    if args.date:
        #If databases aren't filled
        checkEmpty()

        date = args.date

        #Intake current date and get format
        try:
            datetimeObj = datetime.strptime(date, "%m/%d/%Y")
        except ValueError:
            parser.error("Date must be in MM/DD/YYYY format (EX: 02/24/2024)")

        #New format for current date
        newFormat = "%Y-%m-%d 00:00:00"

        #Convert current date into new format
        formattedDate = datetimeObj.strftime(newFormat)
        myquery = {'Build #': {"$regex": f"^{formattedDate}$", "$options": "i"}}
        fallQuery = list(fallCollection.find(myquery))
        springQuery = list(springCollection.find(myquery))
        #Get Current Keys of CSV
        keys = fallQuery[0].keys()

        csvList = dupeChecker(fallQuery,springQuery)

        #Writer
        with open("date.csv",'w',encoding="utf-8" ,newline='') as output:
            writer = csv.DictWriter(output, fieldnames=keys)
            writer.writeheader()
            writer.writerows(csvList)
            
