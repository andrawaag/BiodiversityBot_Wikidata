from wikidataintegrator import wdi_core, wdi_login
import os
import requests, zipfile, io
import pandas as pd
import pprint
import copy
from wikidataintegrator.wdi_helpers import try_write

if "WDUSER" in os.environ and "WDPASS" in os.environ:
    WDUSER = os.environ['WDUSER']
    WDPASS = os.environ['WDPASS']
else:
    raise ValueError("WDUSER and WDPASS must be specified in local.py or as environment variables")

login = wdi_login.WDLogin(WDUSER, WDPASS)

def create_reference(observation_id, license):
    refStatedIn = wdi_core.WDItemID(value='Q16958215', prop_nr='P248', is_reference=True)
    refiNatObservationId = wdi_core.WDString(value=str(observation_id), prop_nr='P5683',is_reference=True)
    refLicense = wdi_core.WDItemID(value=license, prop_nr="P275", is_reference=True)

    reference = [refStatedIn, refiNatObservationId, refLicense]
    return reference


## get images with cc0 license from iNaturalist
download_url = "https://www.inaturalist.org/attachments/flow_task_outputs/1319994/observations-48332.csv.zip?1552507613"
r = requests.get(download_url)
z = zipfile.ZipFile(io.BytesIO(r.content))
print(z.namelist())
df = pd.read_csv(z.open(z.namelist()[0]))

## Set a dictionary to add all Wiidata items IDs that need to be updated
wd_items_ids = dict()
## Iterate over the pandas dataframe

for i, row in df.iterrows():
    if i>10:
        continue ### set a limit to 10 edits while in the bot approval request

    taxon_id = row["taxon_id"]
    observation_id = row["url"].replace("https://www.inaturalist.org/observations/", "").replace("http://www.inaturalist.org/observations/", "")
    image_url = row["image_url"].replace("medium", "original")
    scientific_name = row["scientific_name"]
    license = row["license"]

    print(observation_id, scientific_name, image_url, taxon_id)

    query = """
    SELECT ?item ?itemLabel WHERE {
        ?item wdt:P3151 \""""
    query += str(taxon_id)
    query += """\" .
        FILTER NOT EXISTS {?item wdt:P4765 ?link }
        SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
        }
    """
    # print(query)
    wd = wdi_core.WDItemEngine.execute_sparql_query(query)
    results = wd["results"]["bindings"]

    if len(results) == 1: # only continue if the inat id exists in WD and is unique
        wdid = wd["results"]["bindings"][0]["item"]["value"]
        if wdid not in wd_items_ids.keys():
            wd_items_ids[wdid] = dict()

        # add property P4765
        if "P4765" not in wd_items_ids[wdid].keys():
            wd_items_ids[wdid]["P4765"] = []
        if license != "CC0":
            continue
        reference = create_reference(observation_id, "Q6938433")
        wd_items_ids[wdid]["P4765"].append(wdi_core.WDUrl(image_url, prop_nr="P4765", references=[copy.deepcopy(reference)])) ## TODO:CHange this once the bot deals with CC-BY flavours


pprint.pprint(wd_items_ids)

## collect all populated statements to write to Wikidata
for qid in wd_items_ids.keys():
    data2add = []
    for key in wd_items_ids[qid].keys():
        for statement in wd_items_ids[qid][key]:
            data2add.append(statement)

        wdPage = wdi_core.WDItemEngine(wd_item_id=str(qid.replace("http://www.wikidata.org/entity/", "")), data=data2add)
        pprint.pprint(wdPage.get_wd_json_representation())
        wdPage.write(login, edit_summary="added a URL to a observation of this taxon in iNaturalist with a CC0 license")




