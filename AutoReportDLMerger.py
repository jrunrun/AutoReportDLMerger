import pandas as pd
import os, time, requests, json, locale
from PyPDF2 import PdfFileMerger, PdfFileReader
from shutil import copyfile

print "Generating Reports..."

# Start stopwatch
startTime = time.clock()


# Date and Time stamp for directory name
dateTimeStamp = time.strftime("%Y%m%d_%H%M")

# NOTE! Substitute your own values for the following variables
server_name = "" # Name or IP address of your installation of Tableau Server
user_name = ""    # User name to sign in as (e.g. admin)
password = ""
site_url_id = ""          # Site to sign in to. An empty string is used to specify the default site.
root_path = "" 			# Root directory
inputFile = "./filters.csv" #Location of Filters file

# Read more about URL filter options here:  
# https://onlinehelp.tableau.com/current/pro/desktop/en-us/embed_structure.html

# Read input file that contains list of filters to be applied to views
# For Ochsner, this is a list of Providers Names matching the format contained in the published Tableau Views 
os.chdir(root_path)
Df = pd.read_csv(inputFile)
Filters = Df[Df.columns.values[0]].tolist()
Filters.sort()


print('Report subjects to be processed:')
print('\n')
print('{filters}'.format(filters=Filters))

# Create subdirectory for each filter
for value in Filters:
    os.makedirs(value)

# Create subdirectory called "Merged-Reports"
os.makedirs("Merged-Reports")
merged_dir = os.path.join(root_path,"Merged-Reports")

# Authenticate to Tableau Server API
signin_url = "http://{server}/api/2.5/auth/signin".format(server=server_name)

					
payload = { "credentials": { "name": user_name, "password": password, "site": {"contentUrl": site_url_id }}}
					
headers = {
  'accept': 'application/json',
  'content-type': 'application/json'
}
					
# Send the request to the server
req = requests.post(signin_url, json=payload, headers=headers)
req.raise_for_status()
					
# Get the response
response = json.loads(req.content)
					
# Get the authentication token from the <credentials> element					
token = response["credentials"]["token"]
					
# Get the site ID from the <site> element
site_id = response["credentials"]["site"]["id"]
print('\n')				
print('Sign in to Tableau REST API was successful!')
print('\n')	
print('\tToken: {token}'.format(token=token))
print('\tSite ID: {site_id}'.format(site_id=site_id))
print('\n')	
					
# Set the authentication header using the token returned by the Sign In method.
headers['X-tableau-auth']=token

						
# Process Reports
					
									
token_new = "workgroup_session_id="+token
headers = {
    'Cookie': token_new,
    'Connection': "keep-alive"
    }

view = "Map"

wb_views = ["superfiltertest1/Map", "superfiltertest2/Bar", "superfiltertest3/Treemap"]

for fv in Filters:				
	print('Subject: {filter} is being processed'.format(filter=fv))
	current_dir = os.path.join(root_path,fv)
	os.chdir(current_dir)

	# Create PDF files for each {workbook_view} filtered by {filter}
	for wbv in wb_views:
		url = 'http://{server}/views/{workbook_view}.pdf?Sub-Category={filter}'.format(server=server_name, workbook_view=wbv, filter=fv)
		response = requests.get(url, headers=headers)
		view_name = wbv.split("/")[1]
		outputFile = view_name + "-" + fv + ".pdf"
		with open(outputFile, 'wb') as file:
		    file.write(response.content)
    
	# Create a list of all PDF files in current directory
	filenames_b4 = [f for f in os.listdir(current_dir) if f.endswith("pdf")]    

	# Merge PDF files into single PDF with name "-merged"
	merger = PdfFileMerger()
	for filename in filenames_b4:
	    merger.append(PdfFileReader(open(filename, 'rb')))

	# Save merged PDF in appropriate subdirectory for given {filter}
	outputFile2 = fv + "-" + "merged" + ".pdf"
	merger.write(outputFile2)

	# Copy the merged PDF to 2nd location here: "Merged-Reports"
	src = current_dir + '/{filter}-merged.pdf'.format(filter=fv)
	dst = merged_dir + '/{filter}-merged.pdf'.format(filter=fv)
	copyfile(src, dst)


# Output elapsed time
print "Elapsed time:", locale.format("%.2f", time.clock() - startTime), "seconds"







