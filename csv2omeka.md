# DRAFT! WORK IN PROGRESS.

# About

This is a work-in-progress script to upload an CSV (Comma Separated
Values) file of data to one or more Omeka collections. The purpose of
the script is to allow a tecnically adept person to load data into an
Omeka instance to create an initial repository. It is unlikely that
you would want to maintain a repository using a CSV, the
assumption is that this would be used to 'seed' a repository which
would then be maintained using the normal web UI.

The file can contain:

* Repository items, one per row.
* Files 
* Multi-valued fields that get turned into multiple metadata elements
  in Omeka, eg a comma separated list of contributors in a
  dc:contributor column.


# Quick start

(Assuming you have an Omeka instance with the API turned on and 
the [extended ItemRelations plugin](https://github.com/ozmeka/plugin-ItemRelations).)
Run this, changing the -u and -k parameters to match your repository
api URL and your API key.

```python csv2omeka.py -y -p -c -u http://your-omeka.example/api -k YOUR_API_KEY sample-data/first-fleet-maps.csv```

This should create two collections (maps and people) and a number of
inter-related items. 

# Audience

This document is aimed at technical staff familiar with commandline
systems administration and Python programming, and assumes the reader
may have to do some experimentation, research and problem solving.

# How-to use this script


## Get the script and Python libraries

Install

    git clone https://github.com/uws-eresearch/omekadd.git

Test for missing Python libraries

   cd omekadd
   python xlsx2omeka.py
   sudo easy_install missing libraries until errors cease
  
  
## Set up an Omeka server

* Install Omeka 2.2
* Increase the upload limits in the PHP5.ini file to a big enough number for your project's files
  In /etc/php.ini change these two settings.
```  
   post_max_size = 48M
   upload_max_filesize = 48M
```
  Replace '48M' with the maximum file size you are expecting to upload during your project.

* In the Admin, allow upload of all the file types you have in your data (or allow all)
* Get an API key for a superuser
* Add the following plugins: eResearch version of ItemRelations, Extended Dublin Core


# Get ready to run the script
To get set up:
* Put the address of the server and your API key in ~/.omeka.config, e.g.:
```
{
   "api_url":"http://130.220.210.60/api",
   "key":"apparentlyrandomcharacters"
}
```

* Or pass these detail on the commandline using the -u (URL) and -k (Key) flags (examples below will assume the .omeka.config file exists.



## Set up a CSV file

To structure your CSV file, using a spreadsheet program:
*   Make sure there is an `dc:identifier` column containing an ID which
    is unique to the whole workbook (tip: you can use sequential
    integers using auto-fill in a spreadsheet program but make sure
    not to reuse)
  * Make sure there is a column "dc:type" with the name of an existing
    Item Type for every data row (tip: use -y flag to force item types
    to be auto-created). To make a collection enter pcdm:collection 
  * Make sure there are Omeka metadata elements for each bit of metadata you'd like to import corresponding to the column headers on the worksheet, the script will attempt to find an element match

## Configure file uploads and item-relations

To add files:
* To upload files from the file system, in the `Omeka Mapping` sheet of the mapping spreadsheet:
  * put `yes` in the `File` column for the column in question
  * Make sure that the the paths to the files are either absolute (starting with /) or relative to the data directory, by default this is ./data (relative to where you're running the script) but you can change this by passing a data directory using -d.
* To upload files via a URL, in the `Omeka Mapping` sheet of the mapping spreadsheet, put `yes` in the `Download` column for the field in question.
  The script will cache downloaded files in the data directory and only re-upload to the server if there is a size difference between the size reported by the server from where the files are being downloaed and the cached copy.

To relate items to each other:
*   Make sure the spreadsheet you are using has relations whithin it.
  For example, if you have a number of  `person` items and some `book`
  items (all on their own row) you could relate books to people by:
  * Add a column `REL:dc:creator` 
  * For each book, put the`dc:identifier` of a person into the
  `REL:dc:creator` field.
   To add mulptiple creators:
      * add a '+' to the columns header `REL:dc:creator+`
      *  Put a comma separated list of IDs `"person1, person2, person3"`
  * Run the script once to create all the items, and then again to
    link them to each other.


## Run the initial import

Once you have a spreadsheet, you can run the script and upload data to
an Omeka instance. The first run will attempt to create Omeka items
and collections, one per row (provided the row has (at least) an ID in
the dc:identifier column) and will attempt to upload files from the
local file system and via URLs.


```
## Second or subsequent runs



# Problems, FAQ

## Some or all items from my spreadsheet won't upload

Check that for each row.
* There is an ID in the `dc:identifier` column or another column you specified using the `-i` flag.
* There is an Omeka Type and the Omeka Type exists as an Item Type in your Omeka isntances (or use the `-y` flag to auto-create)

## Some items are coming through without a title but there is a `dc:title` column in my spreadsheet.
Check that there is no space before or after Title in the column-header - sometimes spurious spaces get created by Excel when importing CSV files.

## Some files won't upload

Check the Omeka confiuration allows upload of that file type, and check that the file is within the upload limits you configured on the server see above.



