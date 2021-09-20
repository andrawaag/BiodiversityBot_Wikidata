from wikidataintegrator import wdi_core, wdi_login
import os
import requests, zipfile, io
import pandas as pd
import pprint
import copy

def create_reference(observation_id, license):
    refStatedIn = wdi_core.WDItemID(value='Q16958215', prop_nr='P248', is_reference=True)
    refiNatObservationId = wdi_core.WDString(value=str(observation_id), prop_nr='P5683',is_reference=True)
    refLicense = wdi_core.WDItemID(value=license, prop_nr="P275", is_reference=True)

    reference = [refStatedIn, refiNatObservationId, refLicense]
    return reference

if "WDUSER" in os.environ and "WDPASS" in os.environ:
    WDUSER = os.environ['WDUSER']
    WDPASS = os.environ['WDPASS']
else:
    raise ValueError("WDUSER and WDPASS must be specified in local.py or as environment variables")

login = wdi_login.WDLogin(WDUSER, WDPASS)

## get images with cc0 license from iNaturalist
download_url = "https://www.inaturalist.org/attachments/flow_task_outputs/1319208/observations-47968.csv.zip?1552172607"
r = requests.get(download_url)
z = zipfile.ZipFile(io.BytesIO(r.content))
print(z.namelist())
df = pd.read_csv(z.open(z.namelist()[0]))

## Set a dictionary to add all Wiidata items IDs that need to be updated
wd_items_ids = dict()

i = 0
for i, row in df.iterrows():

    taxon_id = row["taxon_id"]
    observation_id = row["url"].replace("https://www.inaturalist.org/observations/", "").replace("http://www.inaturalist.org/observations/", "")
    image_url = row["image_url"].replace("medium", "original")
    scientific_name = row["scientific_name"]
    license = row["license"]
    scientific_name = row["scientific_name"]
    dutch_name = row["common_name"]

    if not type(scientific_name) is str:
        continue

    query = """
    SELECT ?item WHERE {
    ?item wdt:P31 wd:Q16521 ;
          wdt:P225 \""""
    query += scientific_name
    query += """\" .
        FILTER NOT EXISTS {?item wdt:P3151 ?iNatTaxon .}
    }
    """
    wd = wdi_core.WDItemEngine.execute_sparql_query(query)
    results = wd["results"]["bindings"]
    if len(results) >0:
        print(taxon_id, observation_id, scientific_name, image_url, taxon_id, scientific_name, dutch_name, str(len(results)))
        wdid = wd["results"]["bindings"][0]["item"]["value"]
        if wdid not in wd_items_ids.keys():
            wd_items_ids[wdid] = dict()
         # add property P4765
        if "P4765" not in wd_items_ids[wdid].keys():
            wd_items_ids[wdid]["P4765"] = []
        if "P225" not in wd_items_ids[wdid].keys():
            wd_items_ids[wdid]["P225"] = []
        if "P31" not in wd_items_ids[wdid].keys():
            wd_items_ids[wdid]["P31"] = []
        if license != "CC0":
            continue
        reference = create_reference(observation_id, "Q6938433")
        wd_items_ids[wdid]["P4765"].append(wdi_core.WDUrl(image_url, prop_nr="P4765", references=[
                copy.deepcopy(reference)]))  ## TODO:CHange this once the bot deals with CC-BY flavours
        wd_items_ids[wdid]["P225"].append(wdi_core.WDString(scientific_name, prop_nr="P225", references=[copy.deepcopy(reference)]))
        wd_items_ids[wdid]["dutch_name"] = dutch_name
        wd_items_ids[wdid]["P3151"] = [wdi_core.WDString(str(taxon_id), prop_nr='P3151', references=[copy.deepcopy(reference)])]  ## TODO:CHange this once the bot deals with CC-BY flavours
        wd_items_ids[wdid]["P31"] = [wdi_core.WDItemID("Q16521", prop_nr='P31', references=[
                                       copy.deepcopy(reference)])]  ## TODO:CHange this once the bot deals with CC-BY flavours

        i+=1
        if i>2000:
            break


pprint.pprint(wd_items_ids)
for qid in wd_items_ids.keys():

    data2add = []
    for key in wd_items_ids[qid].keys():
        for statement in wd_items_ids[qid]['P31']:
            data2add.append(statement)
        for statement in wd_items_ids[qid]['P225']:
            data2add.append(statement)
        for statement in wd_items_ids[qid]['P4765']:
            data2add.append(statement)
        for statement in wd_items_ids[qid]['P3151']:
            data2add.append(statement)

        wdPage = wdi_core.WDItemEngine(wd_item_id=str(qid.replace("http://www.wikidata.org/entity/", "")), data=data2add)
        pprint.pprint(wdPage.get_wd_json_representation())
        wdPage.write(login, edit_summary="added a URL to a observation of this taxon in iNaturalist with a CC0 license")

