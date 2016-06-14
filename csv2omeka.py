from omekaclient import OmekaClient
from omekautils import get_omeka_config
from omekautils import create_stream_logger
from sys import stdout, stdin
import argparse
import json
import httplib2
import urlparse
import os
import json
import csv
import shelve
import copy
from pcdmlite.pcdmlite import Item 
from csv2pcdmlite.csv2pcdmlite import CSVData 


""" Uploads a csv file to an Omeka server as a series of items and/or collections, one per line """

def download_and_upload_files(item):
    """Handle any dowloads, cache as files locally, then upload all files"""
    http = httplib2.Http()
    download_this = True
    files = []
    for url_field in item.URLs:
        url = url_field.value
        filename = urlparse.urlsplit(url).path.split("/")[-1]
        new_path = os.path.join(data_dir, str(item.id))
        if not os.path.exists(new_path):
            os.makedirs(new_path)
        file_path = os.path.join(new_path, filename)
        logger.info("Local filename: %s", file_path)

        #Check if we have one the same size already
        if os.path.exists(file_path):
            response, content = http.request(url, "HEAD")
            download_size = int(response['content-length']) if 'content-length' in response else -1
            file_size = os.path.getsize(file_path)
            if download_size == file_size:
                logger.info("Already have a download of the same size: %d", file_size)
                download_this = False

        if download_this:
            try:
                response, content = http.request(url, "GET")
                open(file_path,'wb').write(content)
                logger.info(response)
            except:
                logger.warning("Some kind of download error happened fetching %s - pressing on" % url)

        files.append(file_path)
       
        
    for f in item.files:
        files.append(os.path.join(data_dir, f.value))
        
    for fyle in files:
        logger.info("Uploading %s", fyle)
        try:
            omeka_client.post_file_from_filename(fyle, item.omeka_id )
            
            logger.info("Uploaded %s", fyle)
        except:
            logger.warning("Some kind of error happened uploading %s - pressing on" % fyle)



logger = create_stream_logger('csv2omeka', stdout)



def omekaize(item): #TODO make this a kind of repository item
    dc_set_id = omeka_client.getSetId("Dublin Core",
                                  create=args['create_elements'] )
    type = item.type if item.type != None else args["item_type"]
    item_type_id = omeka_client.getItemTypeId(type, create=args['create_item_types'])
    item.omeka_data =  {"public": args["public"],
                        "item_type" : {"id": item_type_id }}
    

                       
    if item.in_collection != None:
        collection_id = omeka_client.get_collection_id_by_dc_identifier(item.in_collection,
                                                                        name=item.in_collection,
                                                                        create=args['create_collections'],
                                                                        public=args["public"])

        if collection_id != None:
            item.omeka_data["collection"] = {"id": collection_id}


    #Lets deal with DC fields to start with and worry about other namespaces later
    element_texts = []
    for f in item.text_fields:
        if f.namespace.prefix == "dcterms":
             element_id = omeka_client.getElementId(dc_set_id ,f.field_name, create=args['create_elements'] )
             element_text = {"html": False, "text": unicode(f.value)}
             element_text["element"] = {"id": element_id }
             element_texts.append(element_text)
             
    
        item.omeka_data["element_texts"] = element_texts

        
        
def get_old_item(shelf, id):
    return shelf[id] if id in shelf else omekaize(csv2repo.Item())

def save_item(shelf, item):
    new_item = copy.deepcopy(item)
    shelf[id] = new_item

# Define and parse command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument('inputfile', type=argparse.FileType('rb'),  default=stdin, help='Name of input Excel file')
parser.add_argument('-k', '--key', default=None, help='Omeka API Key')
parser.add_argument('-u', '--api_url',default=None, help='Omeka API Endpoint URL (hint, ends in /api)')
parser.add_argument('-d', '--download_cache', default="./data", help='Path to a directory in which to chache dowloads (defaults to ./data)')
parser.add_argument('-p', '--public', action='store_true', help='Make items public')
parser.add_argument('-c', '--create_collections', action='store_true', help='Auto-create missing collections')
parser.add_argument('-e', '--create_elements', action='store_true', help='Auto-create missing element types')
parser.add_argument('-y', '--create_item_types', action='store_true', help='Auto-create missing Item Types')
parser.add_argument('-q', '--quietly', action='store_true', help='Only log errors and warnings not the constant stream of info')
parser.add_argument('-t', '--relation_table', action='store_true', help='Work in relations mode ie look for rdf:subject, rdf:predicate, rdf:object triples rather than Items (objects and collections)')
parser.add_argument('-r', '--relate', action='store_true', help='Relate items to each other')
parser.add_argument('-i', '--item_type', default="Text", help='Item type to us if there is no dc:type in the input row (Defaults to Text).')
parser.add_argument('-n', '--in_collection', default="None", help='Collection to use if there is no dc:type in the input row (Defaults to None).')
args = vars(parser.parse_args())

if not args['api_url'] or not args['key']:
    config = get_omeka_config()

endpoint = args['api_url'] if args['api_url']  else config['api_url']
apikey   = args['key'] if args['api_url'] else config['key']


omeka_client = OmekaClient(endpoint.encode("utf-8"), logger, apikey)
inputfile = args['inputfile']
data_dir = args['download_cache']

# Because we can't efficiently query omeka via API, need to cache data about
# what gets uploaded and what ID it gets
shelf_file = "%s_item_cache" % endpoint.replace("/","_").replace(":",".")
shelf = shelve.open(shelf_file)



if args["quietly"]:
    logger.setLevel(30)


if args['relation_table']:
    reader = csv.DictReader(inputfile)
    fieldnames = reader.fieldnames
    if not("rdf:subject" in fieldnames and
           "rdf:predicate" in fieldnames and
           "rdf:object" in fieldnames):
           logger.error("CSV file needs rdf:subject, rdf:predicate and rdf:object columns")
           exit()
           
    for row in reader:
        s = get_old_item(shelf, row['rdf:subject']).omeka_id
        o = get_old_item(shelf, row['rdf:object']).omeka_id
        predicate_field = csv2repo.Field(row['rdf:predicate'].lower())
        p = omeka_client.getRelationPropertyIdByLocalPart(predicate_field.namespace.prefix, predicate_field.field_name)
        #print s, row['rdf:predicate'], predicate_field.namespace.prefix, predicate_field.field_name, o
        if o != None and s != None and p != None:
                logger.info("Relating this item %s to another. Property %s, target %s", s, p, o)
                omeka_client.addItemRelation(s, p, o)
else:
    csv_data = CSVData(inputfile)
    csv_data.get_items()
 
        
    for collection in csv_data.collections:
        id = collection.id
        title = collection.title
        if id != None:
            collection_id = omeka_client.get_collection_id_by_dc_identifier(id, name=title, create=args['create_collections'], public=args["public"])
            print "Collection ID", collection_id

    uploaded_item_ids = []
    total_rows = len(csv_data.items)
    row_num = 0
    for item in csv_data.items:
        print "Processing %s/%s" % (row_num, total_rows)
        row_num += 1
        id = item.id
        
        if id != None:
            if item.title == None or item.title == "":
                item.title == "Untitled %s" % str(id)
          
            if item.in_collection == None and args["in_collection"] != None:
                item.in_collection = args["in_collection"]
               
                
            #TODO - make this a parameter with a default
            previous_item = get_old_item(shelf, id)
            logger.info("Processing item with Dublin Core ID %s", id)
            omekaize(item)
            jsonstr = json.dumps(item.omeka_data)
            # Reupload
            if previous_item != None and previous_item.id != None:
                previous_id = previous_item.omeka_id
                logger.info("Re-uploading %s", previous_id)
                response, content = omeka_client.put("items" , previous_id, jsonstr)
                new_item = json.loads(content)
                #Looks like the ID wasn't actually there, so get it to mint a new one
                if response['status'] == '404':
                    logger.info("retrying")
                    response, content = omeka_client.post("items", jsonstr)

            else: #Or upload new one
                logger.info("Uploading new item")
                response, content = omeka_client.post("items", jsonstr)


            # Should have new (or old) item now
            new_item = json.loads(content)
            if  'id' in new_item:
                item.omeka_id = str(new_item['id'])
                save_item(shelf, item)
                download_and_upload_files(item)
                
                if args['relate']:
                    # Relate to other items
                    for r in item.relations:
                        property_id = omeka_client.getRelationPropertyIdByLocalPart(r.namespace.prefix, r.field_name)
                        object_item =  get_old_item(shelf, r.value)
                        object_id = object_item.omeka_id if object_item != None else None
                        if object_id != None and property_id != None:
                            logger.info("Relating this item %s to another. Property %s, target %s", item.omeka_id, property_id, object_id)
                            omeka_client.addItemRelation(item.omeka_id, property_id, object_id)
                
                    
            else:
                logger.error("Uploading failed for item %s %s" % (id, content))


