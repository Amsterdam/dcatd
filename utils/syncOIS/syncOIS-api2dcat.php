<?php
require_once("dcat.php");

$dcat_env = getenv('DCAT_ENVIRONMENT');
if(!$dcat_env || $dcat_env != 'prod') {
    $env_prefix = 'acc.';
} else {
    $env_prefix = '';
}

$test_env = getenv('DCAT_DO_TEST');
if(!$dcat_env || $dcat_env != 'false') {
    $do_test = true;
} else {
    $do_test = false;
}

define("DCAT_URL", "https://{$env_prefix}api.data.amsterdam.nl/dcatd/");
define("OIS_URL","https://www.ois.amsterdam.nl/api/get-items/20000");
define("DCAT_USER", getenv("DCAT_USER"));
define("DCAT_PASSWORD",getenv("DCAT_PASSWORD"));
      
error_reporting(E_ALL ^E_NOTICE ^E_WARNING);
set_time_limit(600);
ini_set('memory_limit', '256M');

class SyncOIS{
    var $url;
    var $onderwerpen;
    var $bestanden;
    var $groupmapping;
    var $dcat;
    var $sets;
        
        
    /**
    * Constructor.
    * Sets mapping for groups, from categories OIS is using to groups in Catalogus
    * 
    */
    function SyncOIS($do_test){
        $this->groupmapping =  Array(
            "Kerncijfers" => "bevolking",
            "Bevolking" => "bevolking",
            "Openbare orde en veiligheid" => "openbare-orde-veiligheid",
            "Werk en inkomen" => "werk-inkomen",
            "Zorg" => "zorg-welzijn",
            "Gezondheid" => "zorg-welzijn",
            "Onderwijs" => "educatie-jeugd-diversiteit",
            "Verkeer en infrastructuur" => "verkeer-infrastructuur",
            "Openbare ruimte en groen" => "openbare-ruimte-groen",
            "Cultuur en monumenten" => "toerisme-cultuur",
            "Milieu en water" => "milieu-water",
            "Sport en recreatie" => "sport-recreatie",
            "Economie en haven" => "economie-haven",
            "Stedelijke ontwikkeling" => "stedelijke-ontwikkeling",
            "Middelen" => "bestuur-en-organisatie",
            "Bestuur en concern" => "bestuur-en-organisatie",
            "Tijdreeksen" => "bevolking",
            "Prognoses" => "bevolking",
            "Educatie" => "educatie-jeugd-diversiteit",
            "Milieu" => "milieu-water",
            "Verkiezingen" => "verkiezingen",
            "Veiligheid" => "openbare-orde-veiligheid",
            "Economie" => "economie-haven",
            "Inkomen en sociale zekerheid" => "werk-inkomen",
            "Gezondheid en welzijn" => "zorg-welzijn",
            "Verkeer en vervoer" => "verkeer-infrastructuur",
            "Natuur en milieu" => "milieu-water",
            "Toerisme" => "toerisme-cultuur",
            "Bouwen en wonen" => "wonen-leefomgeving",
            "Politiek" => "verkiezingen",
            "Bestuur" => "bestuur-en-organisatie",
            "Openbare ruimte" => "openbare-ruimte-groen",
            "Kaart" => "geografie"
        );
        
        $this->new_sets = 0;
        $this->updated_sets = 0;
        $this->deleted_sets = 0;
         
        $this->readAPI();
        $this->buildDatasetsFromAPI();     
           
        $this->dcat = new DCAT(DCAT_URL,DCAT_USER, DCAT_PASSWORD);
        $this->readDatasetsFromDCAT();
        $this->sync($do_test);
    }
    
    /**
    * Read API from OIS website and fills $this->onderwerpen with all sets and files as available in OIS website
    * 
    */
    
    function readAPI(){
        $this->onderwerpen = [];
        $items = json_decode(file_get_contents(OIS_URL));
        
        foreach($items->in as $item){
            $this->addItemFromAPI($item);
        }
    }
    
    /**
    * Recursive function to read parts of API of OIS website
    * 
    * @param mixed $item Item as read from OIS website API
    */
   
    function addItemFromAPI($item){
        if($item->osid > 0 && !$this->onderwerpen[$item->osid]){
            $this->onderwerpen[$item->osid] = $item;
            $this->onderwerpen[$item->osid]->bestanden = [];
             $bestanden = json_decode(file_get_contents("https://www.ois.amsterdam.nl/api/get-bestanden/". $item->osid));
             foreach($bestanden->bestanden as $bestand){
                 $this->onderwerpen[$item->osid]->bestanden[] = $bestand;
             }
             foreach($item->in as $child){
                $this->addItemFromAPI($child);
             }
             unset($this->onderwerpen[$item->osid]->in);
        }
    }
    
    /**
    * Takes all $this->onderwerpen as read from OIS website API and transforms these into DCAT datasets in $this->sets
    * 
    */
    function buildDatasetsFromAPI(){
        foreach($this->onderwerpen as $onderwerp){
            if(count($onderwerp->bestanden) > 0){
                $set = $this->buildSet($onderwerp);
                if($set) $this->sets[] = $set;
            }
        }
    }
    
    /**
    * Takes a 'item' specified in OIS website API and transforms this into a DCAT-valid dataset. 
    * 
    * @param mixed $onderwerp as specified in OIS website
    * @return stdClass DCAT-valid dataset
    */
    
    function buildSet($onderwerp){
        $id = $onderwerp->osid;
        $tags = Array();
        
        list($fenc, $gebied, $thema, $subthema) = explode(" > ",$onderwerp->path);
        if($gebied == "Feiten en cijfers") $gebied = $fenc;
        
        if(trim($thema) == "") $thema = "Feiten en cijfers";
        $titel = $thema;
        if(trim($subthema) <> "") $titel .= " - ". $subthema;
        $titel .= " (". $gebied .")";  

        $notes = "<p>Diverse datasets met statistieken van Onderzoek, Informatie en Statistiek.</p><p>Thema: ". $thema;
        if(trim($subthema) <> "") $notes .= ", <br/>Onderwerp:  ". $subthema;
        if(trim($gebied) <> "") $notes .= ", <br/>Detailniveau: ". $gebied ."</p>";
                             
                             
        if(!$this->groupmapping[$thema]){
            $group = Array(["theme:Bevolking"]);
        } else {
            $group = Array(["theme:".$this->groupmapping[$thema]]);            
        }


        $resources = Array();
        //Fields -- namespaces doesn't allow direct usage
        $p_title = "dct:title";
        $p_url = "dcat:accessURL";
        $p_resourcetype = "ams:resourceType";
        $p_distributiontype = "ams:distributionType";
        $p_mediatype = "dcat:mediaType";
        $p_classification = "ams:classification";
        $p_license = "dct:license";
        $p_modified = "dct:modified";
        
        foreach($onderwerp->bestanden as $bestand){
            $fname = explode(".",$bestand->bestand->filename);
            if(in_array($fname[count($fname)-1], ["xlsx","xls","zip"])){
                $dist = new stdClass();
                $url = "https://www.ois.amsterdam.nl/downloads/".$fname[count($fname)-1]."/". $bestand->bestand->filename;
                
                $dist->$p_title = $bestand->bestand->titel;
                $dist->$p_url = $url;
                $dist->$p_resourcetype = "data";
                $dist->$p_distributiontype = "file";
                $dist->$p_mediatype = "application/vnd.ms-excel";
                $dist->$p_classification = "public";
                $dist->$p_license = "cc-by";
                
                //API doesn't include publication date of file/resource. Using current date.
                $dist->$p_modified = date("Y-m-d");
                
                $resources[] = $dist;
                
                if(!in_array($bestand->label,$tags)){
                    foreach(explode(",", $bestand->label) as $tag){
                        $tags[] = trim(str_replace(["\\","/","&"],"-",$tag));
                    }
                }
                
            }
        }
        
        if(count($resources) > 0){
            $set = new stdClass();

            //Fields -- namespaces doesn't allow direct usage
            $p_title = "dct:title";
            $p_description = "dct:description";
            $p_status = "ams:status";
            $p_distribution = "dcat:distribution";

            $p_theme = "dcat:theme";
            $p_keywords = "dcat:keyword";
            $p_license = "ams:license";
            $p_authority = "overheid:authority";
            $p_id = "@id";
            $p_identifier = "dct:identifier";
            $p_publisher = "dtc:publisher";
            $p_pubname = "foaf:name";
            $p_pubmail = "foaf:mbox";
            
            $p_accrual = "dct:accrualPeriodicity";
            $p_temporal = "ams:temporalUnit";
            $p_language = "dct:language";
            $p_owner = "ams:owner";
            $p_contact = "dcat:contactPoint";
            $p_contact_name = "vcard:fn";
            $p_contact_mail = "vcard:hasEmail";
            $p_doel = "overheidds:doel";
            
            $p_dates = "foaf:isPrimaryTopicOf";
            $p_dates_issued = "dct:issued";
            $p_dates_modified = "dct:modified";
            
            $set->$p_title = $titel;
            $set->$p_description = $notes;
            $set->$p_status = "beschikbaar";
            
            $set->$p_distribution = $resources;
            
            $set->$p_doel = "Verzamelen statistieken";
            
            $set->$p_dates = new stdClass();
            $set->$p_dates->$p_dates_issued = date("Y-m-d");
            $set->$p_dates->$p_dates_modified = date("Y-m-d");
            
            $set->$p_accrual = "unkown";
            $set->$p_temporal = "na";
            $set->$p_language = "lang1:nl";
            $set->$p_owner = "Gemeente Amsterdam, Onderzoek, Informatie en Statistiek";

            $set->$p_contact = new stdClass();
            $set->$p_contact->$p_contact_name = "Gemeente Amsterdam, Onderzoek, Informatie en Statistiek";
            $set->$p_contact->$p_contact_mail = "algemeen.OIS@amsterdam.nl";
            
            $set->$p_publisher = new stdClass();
            $set->$p_publisher->$p_pubname = "Gemeente Amsterdam, Onderzoek, Informatie en Statistiek";
            $set->$p_publisher->$p_pubmail = "algemeen.OIS@amsterdam.nl";
            
            $set->$p_theme = $group;
            $set->$p_keywords = $tags;
            $set->$p_license = "cc-by";
            $set->$p_authority = "overheid:Amsterdam";
            $set->$p_id = "ams-dcatd:ois-". $id;
            $set->$p_identifier = "ois-".$id;
            
            return $set;
        }
        
    }    
    
    /**
    * Read datsets from DCAT API
    * 
    */
    function readDatasetsFromDCAT(){
        $this->dcat->getDatasets();
    }
    
    /**
    * Sync the datasets build from OIS website API with the the current datasets in DCAT API.
    * 
    * @param boolean $test if true sync will only output results of sync and will not change anything to DCAT
    */ 
    function sync($test = false){
        $p_identifier = "dct:identifier";
        $p_id = "@id";
        $p_title = "dct:title";
        $p_status = "ams:status";

        //For each dataset from API, check if available in DCAT 
        foreach($this->sets as $set){
            print("<HR>{$set->$p_identifier}({$set->$p_title})<BR>");
            $matched_set = null;
            foreach($this->dcat->datasets as $dcatset){
                if($dcatset->$p_identifier == $set->$p_identifier || $dcatset->$p_id == $set->$p_id || $dcatset->$p_title == $set->$p_title){
                    $matched_set = $dcatset;
                    break;
                }
            }
            if($matched_set){
                //Use id and identifier from DCAT API for update
                $set->$p_id = $matched_set->$p_id;
                $set->$p_identifier = $matched_set->$p_identifier;
                
                //Check if resources need synchronisation
                $syncset = $this->syncDistribution($set, $matched_set);
                if($syncset["sync_needed"]){
                    //update dataset
                    if(!$test) $this->updateSet($syncset["set"]);
                    print("Dataset ge-updated met nieuwe links.");
                } else {
                    //No action required
                    print("<strong>Match found. No sync needed.</strong>");
                }
            } else {
                //create dataset
                if(!$test) $this->createSet($set);
                print("No match found, dataset created");
            }
            print("\n");
        }
        //For each OIS-dataset in DCAT, check if it still exists in Excel
        //TODO: this won't work if we don't use 'ois-xxxxx' id's! Does work for initial sync with 'old' OIS-datasets.
        foreach($this->dcat->datasets as $set){
            if(substr($set->$p_identifier,0,4) == "ois-"){
                $set_onderwerp = substr($set->$p_identifier,4);
                $found = false;
                foreach($this->onderwerpen as $onderwerp){
                    if($onderwerp->osid == $set_onderwerp) $found = true;
                }
                if(!$found & $set->$p_status == "beschikbaar"){
                    //update status dataset to 'niet beschikbaar' o.i.d.
                    if(!$test) $this->deleteSet($set);
                    print("<HR>". $set->$p_identifier ."<BR>Bestaat niet meer. Status aangepast naar 'niet beschikbaar'");
                }
            }
        }
    }
    
    /**
    * For a set that is available in both OIS API and DCAT API, check if there are any changes that need to be synced
    * 
    * @param mixed $set dataset from OIS API, in DCAT-format
    * @param mixed $matched_set dataset from DCAT API
    * @returns array containing boolean "sync_needed" and DCAT dataset to be uploaded
    */
    function syncDistribution($set, $matched_set){
        $sync_needed = false;
        $p_distribution = "dcat:distribution";
        $p_url = "dcat:accessURL";
        
        if(count($set->$p_distribution) != count($matched_set->$p_distribution)) $sync_needed = true;
        
        
        $distribution = $set->$p_distribution;
        foreach($distribution as $key => $resource){
            $matched = false;
            foreach($matched_set->$p_distribution as $resource2){
                if($resource->$p_url == $resource2->$p_url){
                    $distribution[$key] = $resource2;
                    //Copy distribution from DCAT, to keep persistent urls
                    $matched = true;
                    break;
                }
            }
            if(!$matched) $sync_needed = true;
        }
        $set->$p_distribution = $distribution;
        
        return ["sync_needed" => $sync_needed, "set" => $set];
    }
    
    function updateSet($set){
        $this->updated_sets += 1;
        $this->putSet($set);
    }
    
    function createSet($set){
        $p_id = "@id";
        $p_identifier = "dct:identifier";
        unset($set->$p_id);
        unset($set->$p_identifier);
        //Unset id and identifier. Let DCAT create a new random Id.

        $this->new_sets += 1;
        $this->postSet($set);
    }
    
    function deleteSet($set){
        $p_status = "ams:status";
        $set->$p_status = "niet beschikbaar";

        $this->deleted_sets += 1;
        $this->putSet($set);
    }
    
    function putSet($set){
        $this->dcat->putSet($set);
        //print("<HR><PRE>"); print_r($set); print("</PRE>");
    }
    
    function postSet($set){
        $this->dcat->postSet($set);
        //print("<HR><PRE>"); print_r($set); print("</PRE>");
    }
}

print("\n\r\n\r<HR>Start - ". date("Y-m-d H:i:s"));
print("\nDCAT_URL: " . DCAT_URL . ", DCAT_DO_TEST: $do_test\n\n");

$sync = new SyncOIS($do_test);

print("\n\r\n\r<HR>OK - ". date("Y-m-d H:i:s"));
print("\n\r". $sync->new_sets ." nieuwe datasets, ". $sync->updated_sets ." updated datasets, ". $sync->deleted_sets ." verwijderd\n");
?>