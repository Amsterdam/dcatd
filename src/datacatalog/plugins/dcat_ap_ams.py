import datetime

from aiopluggy import HookimplMarker
import bleach
from pyld import jsonld

from datacatalog import dcat

hookimpl = HookimplMarker('datacatalog')

_SCHEMA = 'dcat-ap-ams'
_BASE_URL = 'http://localhost/'


@hookimpl
def initialize_sync(app):
    global _BASE_URL
    _BASE_URL = app.config['web']['baseurl']


@hookimpl
def mds_name():
    return _SCHEMA


@hookimpl
def mds_canonicalize(data: dict) -> dict:
    expanded = jsonld.expand(data)
    return jsonld.compact(expanded, context())


@hookimpl
def mds_json_schema() -> dict:
    return DATASET.schema


@hookimpl
def mds_full_text_search_representation(data: dict) -> str:
    return DATASET.full_text_search_representation(data)


@hookimpl
def mds_context() -> dict:
    return context()


def context(base_url=None) -> dict:
    if base_url is None:
        base_url = _BASE_URL
    return {
        'ams': 'http://datacatalogus.amsterdam.nl/term/',
        'ams-dcatd': base_url + 'datasets/',
        'ckan': 'https://ckan.org/terms/',
        'class': 'ams:class#',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'dcat': 'http://www.w3.org/ns/dcat#',
        'dct': 'http://purl.org/dc/terms/',
        'foaf': 'http://xmlns.com/foaf/0.1/',
        'lang1': 'http://id.loc.gov/vocabulary/iso639-1/',
        'lang2': 'http://id.loc.gov/vocabulary/iso639-2/',
        'org': 'ams:org#',
        # Volgens dcat-ap-nl '.../term', maar dat kan niet. Zucht...
        # Volgens allerlei andere overheidsdocumenten:
        'overheid': 'http://standaarden.overheid.nl/owms/terms/',
        # Zelf verzonnen; juiste waarde nog opzoeken [--PvB]
        'overheidds': 'http://standaarden.overheid.nl/owms/terms/ds#',
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
        'skos': 'http://www.w3.org/2004/02/skos/core#',
        'theme': 'ams:theme#',
        'time': 'http://www.w3.org/2006/time#',
        'vcard': 'http://www.w3.org/2006/vcard/ns#',
        'dcat:dataset': {'@container': '@list'},
        'dcat:distribution': {'@container': '@set'},
        'dcat:keyword': {'@container': '@set'},
        'dcat:landingpage': {'@type': '@id'},
        'dcat:theme': {'@container': '@set', '@type': '@id'},
        'dct:issued': {'@type': 'xsd:date'},
        'dct:language': {'@type': '@id'},
        'dct:modified': {'@type': 'xsd:date'},
        'foaf:homepage': {'@type': '@id'},
        'foaf:mbox': {'@type': '@id'},
        'vcard:hasEmail': {'@type': '@id'},
        'vcard:hasURL': {'@type': '@id'},
        'vcard:hasLogo': {'@type': '@id'}
    }


class Markdown(dcat.String):
    def __init__(self, *args, format=None, **kwargs):
        assert format is None
        super().__init__(*args, **kwargs)

    def full_text_search_representation(self, data: str):
        return bleach.clean(data, tags=[], strip=True)


LANGUAGE = dcat.Enum(
    [
        ('lang1:nl', "Nederlands"),
        ('lang1:en', "Engels")
    ],
    title="Taal",
    # description="De taal van de gegevensset",
    default='lang1:nl',
    required=True
)

THEME = dcat.Enum(
    [
        ('theme:bestuur-en-organisatie', "Bestuur en organisatie"),
        ('theme:bevolking', "Bevolking"),
        ('theme:dienstverlening', "Dienstverlening"),
        ('theme:economie-haven', "Economie & Haven"),
        ('theme:educatie-jeugd-diversiteit', "Educatie, Jeugd & Diversiteit"),
        ('theme:energie', "Energie"),
        ('theme:geografie', "Geografie"),
        ('theme:milieu-water', "Milieu & Water"),
        ('theme:openbare-orde-veiligheid', "Openbare orde & veiligheid"),
        ('theme:openbare-ruimte-groen', "Openbare ruimte & groen"),
        ('theme:sport-recreatie', "Sport & recreatie"),
        ('theme:stedelijke-ontwikkeling', "Stedelijke ontwikkeling"),
        ('theme:toerisme-cultuur', "Toerisme & cultuur"),
        ('theme:verkeer-infrastructuur', "Verkeer & Infrastructuur"),
        ('theme:verkiezingen', "Verkiezingen"),
        ('theme:werk-inkomen', "Werk & Inkomen"),
        ('theme:wonen-leefomgeving', "Wonen & leefomgeving"),
        ('theme:zorg-welzijn', "Zorg & welzijn")
    ]
)

KEYWORD = dcat.PlainTextLine(
    examples=['14.000 ft', '2.5D', '20Ke', '360 graden foto', '3D',
              '50 dbA-contour', 'AHN', 'API', 'Afval', 'Aikido', 'Amersfoort',
              'Amsterdam', 'Amsterdam Zuidoost', 'Apotheek', 'Arbeidsmarkt', 'Arena',
              'Auto', 'BAG', 'BI', 'BIG', 'BRK', 'BRT', 'BSO', 'Badminton',
              'Basismeetset', 'Basisregistratie', 'Basisregistratie kadaster',
              'Basketbal', 'Bedrijfstak', 'Beperkingengebied', 'Bestemming', 'Boksen',
              'Boswet', 'Buitenschoolse', 'Buurtcombinaties', 'Buurten', 'CBS',
              'CCTV', 'CIR', 'COROP', 'Capoeira', 'Cijfers', 'City', 'CitySDK',
              'Dans', 'Data', 'Datapunt', 'Demografische druk', 'Economie', 'Energie',
              'Europa', 'Europe', 'European', 'Europees', 'Evenementen', 'Feiten',
              'Fiets', 'GGD', 'Gastouderopvang', 'Gastouders', 'Gebiedsindeling',
              'Gebiedsindelingstadsdelen', 'Gehandicaptenparkeerplaatsen',
              'Grijze druk', 'Groene druk', 'Grofvuil', 'Groot-Amsterdam',
              'Grootschalig', 'H2020', 'HIV', 'HR', 'Handelsregister', 'Hockey',
              'Horeca Informatie Systeem', 'Horizon 2020', 'Huddesteen', 'ICC', 'ICT',
              'IV3', 'Industrielawaai', 'Infrastructuur', 'Innovatie', 'Judo', 'KBKA',
              'KDV', 'Kadaster', 'Kamer', 'Kamer van Koophandel',
              'Kamer van koophandel', 'Kanoën', 'Karate', 'Kinderdagverblijf',
              'Kinderen', 'Klimmen', 'Korfbal', 'Krav', 'Krijgskunst', 'KvK', 'LIB',
              'LIB-4', 'LVNL', 'Leven', 'Linked', 'Luchthavenindelingbesluit', 'MIT',
              'MOOR', 'MORA', 'Maga', 'Metropoolregio Amsterdam', 'Mismatch', 'NAP',
              'NEN', 'NPR', 'Normaal Amsterdams Peil', 'OV', 'Omnisportvereniging',
              'Onderzoek', 'Opleiding', 'Opvang', 'PC4', 'PC5', 'PC6', 'PM10',
              'PM2.5', 'PP6', 'PR', 'PSZ', 'Parkeren', 'Parlement', 'Peuterspeelzaal',
              'Peuterspeelzalen', 'Plusnet', 'Postcode', 'Postcode6', 'Postcodes',
              'Provinciale', 'RCE', 'RD', 'RDA', 'RGB', 'RVE', 'RVO', 'RWS',
              'Rijkswaterstaat', 'SDK', 'Schaken', 'Schietsportvereniging',
              'Schiphol', 'Sjoelen', 'Sportschool', 'Stadsdelen', 'Staten',
              'Statistiek', 'Taekwon-Do', 'Tafeltennis', 'Talent voor de Toekomst',
              'Tennis', 'Top10NL', 'Top50NL', 'Turnen', 'Tweede', 'Tweede Kamer',
              'Tweede kamer', 'UNESCO', 'UWV', 'Ultracam Eagle camera', 'VGO', 'VOR',
              'VVE', 'Voetbal', 'Voetganger', 'Volleybal', 'WBSO', 'WKO', 'WOII',
              'Wegenverkeerswet', 'West', 'Wkpb', 'Yoga', 'Zelfverdediging',
              'Ziggo dome', 'Zomerse', 'Zwemmen', 'aanbieden grofvuil', 'aanbod',
              'aanduiding in onderzoek', 'aangewezen', 'aanhoudingen', 'aantal',
              'aantal kamers', 'aantasting', 'accounts', 'achtergrond',
              'activiteiten', 'actueel', 'actueel hoogtebestand Nederland',
              'adressen', 'afval', 'afval ophaalgebied', 'afval ophaalgebieden',
              'afvalbak', 'afvalbakken', 'afvalcontainers', 'afvalophaalgebied',
              'afvalophaalgebieden', 'afvalpunt', 'afvalregels',
              'afvalregels per locatie', 'afvalscheiding', 'afweergeschut', 'agenda',
              'agent', 'alcoholverbodgebieden', 'amsterdam', 'amsterdam\n', 'and',
              'apotheken', 'appartement', 'appartementen', 'appartementsrecht',
              'appartementsrechten', 'arbeidsmarkt', 'arbeidsongeschiktheid',
              'arbeidsproductiviteit', 'archeologie', 'architect', 'architecten',
              'architectuur', 'armoede', 'artsen', 'atcb', 'atelierpand',
              'attracties', 'auto', 'autobezit', 'autos', 'balie', 'banen', 'bar',
              'barometer', 'basiskaart', 'basisonderwijs', 'basisregistratie',
              'basisregistratie adressen en gebouwen', 'basisscholen', 'basisschool',
              'basisschooladviezen', 'baten', 'bebouwde kom', 'bedden', 'bedrijf',
              'bedrijfstak', 'bedrijfsvaerzamelgebouwen', 'bedrijfsvestigingen',
              'bedrijven', 'beeldbank', 'beelden', 'beeldhouwkunst', 'begroting',
              'bekendmakingen', 'bekeuringen', 'belang', 'belangenbehartiging',
              'belastingen', 'belemmering', 'belemmeringen', 'beperking',
              'beperkingen', 'beroepsbevolking', 'beroepsonderwijs',
              'beschermde dorpsgezichten', 'beschermde stadsgezichten', 'beschikbaar',
              'beschikbaarheid', 'bestedingen', 'bestemmingsplan',
              'bestemmingsplannen', 'beurs', 'bevolking', 'bevolkingsdichtheid',
              'bevolkingsgroei', 'bevolkingsprognose', 'bezetting', 'bezettingsgraad',
              'bezienswaardigheden\n', 'bi', 'bijen', 'bijstand', 'bijzonder',
              'biologische', 'bioscoop', 'blokeenheid', 'bodemkwaliteit', 'boeken',
              'boeren', 'boerenmarkten', 'bom', 'bomen', 'bommenkaart', 'boom',
              'boswet', 'bout', 'bouten', 'bouw', 'bouwblok', 'bouwblokken',
              'bouwblokzijde', 'bouwen', 'bouwjaar', 'bouwjaren', 'bouwrijp',
              'bouwvergunning', 'braakliggend', 'branches', 'brand', 'branden',
              'brandweer', 'broedplaats', 'bromfiets', 'brug', 'bruggen', 'buddy',
              'budget', 'buien', 'bureau', 'burgerlijke', 'burgerlijke staat', 'bus',
              'businesslocatie', 'bussen', 'buurt', 'buurtcentra', 'buurtcentrum',
              'buurtcombinatie', 'buurtcombinaties', 'buurten', 'buurthuis',
              'buurthuizen', 'buurtindeling', 'buurtwerk', 'cabaret', 'cafe', 'cafes',
              'cameras', 'capaciteit', 'cartografie', 'casino', 'catalogus', 'cbs',
              'centrum', 'chemisch afval', 'circulaire economie', 'circus', 'cito',
              'classificatie', 'clinics', 'cohesie', 'collectie', 'collectief',
              'compleet', 'congres', 'congressen', 'containers', 'corporaties',
              'creatieve industrie', 'csv', 'cultureel', 'cultuur', 'cultuurhistorie',
              'dagbesteding', 'daken', 'daklozen', 'daklozenzorg', 'dans', 'data',
              'deformatie', 'dementie', 'demografie', 'detail', 'detailhandel',
              'detaillering', 'dichtgetimmerd', 'dienst werk en inkomen', 'diensten',
              'dienstencentra', 'dienstverlening', 'distribution', 'documenten',
              'doden', 'doelgroepleerlingen', 'doodsoorzaken', 'drempels',
              'drinkwater', 'drugs', 'drukte', 'dubbelglas', 'duurzaamheid',
              'echtscheidende amsterdammer', 'echtscheiding', 'echtscheidingen',
              'ecologie', 'ecologisch', 'ecologische', 'economie',
              'economisch verkeer', 'eik', 'eiken', 'eindtoets', 'elektriciteit',
              'elektrisch', 'elektrische', 'en', 'energie', 'energielabels',
              'energieverbruik', 'erfpacht', 'eten', 'etnische groepen',
              'evenementen', 'evenementenvergunning', 'excel', 'exploitatie',
              'exploitatievergunning', 'explosieven', 'export', 'exposities',
              'faillissementen', 'fauna', 'faunapassage', 'feitelijk gebruik',
              'festivals', 'fiets', 'fietsen', 'fietsenstalling', 'fietsnetwerk',
              'fietspaden', 'files', 'film', 'filtering', 'financien',
              'financiële instellingen', 'fontein', 'food trucks', 'forensisch arts',
              'fotos', 'functie', 'functiekaart', 'functies', 'fundering',
              'funderinghoogte', 'fysiotherapeuten', 'fysiotherapie', 'galleries',
              'gas', 'gbk', 'gbka', 'gbkn', 'gebieden', 'gebieden\n',
              'gebiedsgericht werken', 'gebiedsindeling', 'geboorte', 'gebouw',
              'gebouwen', 'gebouwhoogte', 'gebouwhoogtes', 'gebruiksdoel',
              'gebruiksdoelen', 'gebruiksvergunning', 'gehandicapt',
              'gehandicaptenparkeerplaatsvergunning', 'geluid', 'geluidshinder',
              'geluidskaart', 'geluidsoverlast', 'geluidzones', 'gemeente',
              'gemeentebegroting', 'gemeentefonds', 'gemeentelijk monument',
              'gemeentelijke beperkingenregistratie', 'gemeenteraad',
              'gemeenteraadsleden', 'gemeenterekening', 'geografie', 'geometrie',
              'geothermie', 'geslaagden', 'geslachtsziekten', 'gevaarlijke',
              'gewicht', 'gewonden', 'gezondheid', 'gezondheidszorg',
              'gezoneerd industrieterrein', 'geïnterpoleerd', 'ggz', 'gierzwaluw',
              'gis', 'gladheid', 'glas', 'glasbak', 'goederen', 'goods', 'gracht',
              'grachten', 'granaat', 'grid', 'groei', 'groeicijfers', 'groen',
              'groene', 'groenvoorziening', 'grof vuil', 'grond', 'grondgebied',
              'grondgebruik', 'grondresolutie', 'grootschalig', 'grootschalige',
              'grootschalige kaart', 'grootschalige topografie',
              'grootstedelijk gebied', 'grootstedelijke gebieden', 'gvb', 'gymzaal',
              'gymzalen', 'halte', 'haltes', 'handel', 'haven', 'havens', 'hbo',
              'herbestemming', 'herhalingsmeting', 'herkomst', 'herrie', 'hinder',
              'historie', 'historisch', 'hogescholen', 'homo', 'honing',
              'hoofdbewoners', 'hoofdgroenstructuur', 'hoogopgeleide', 'hoogte',
              'hoogtemodel', 'hoogtes', 'horeca', 'hotel', 'hotelloods', 'hotels',
              'houtopstanden', 'huisarts', 'huisartspraktijk', 'huishoudelijk',
              'huishoudens', 'huishoudenstypen', 'huisletter', 'huisletters',
              'huisnummer', 'huisnummers', 'huisnummertoevoeging',
              'huisnummertoevoegingen', 'huisvesting', 'huisvuil',
              'huisvuil ophaalgebied', 'huizen', 'hulp', 'hulpverlening', 'huren',
              'huur', 'huurprijs', 'huursubsidie', 'huurtoeslag', 'huurwoningen',
              'huwelijk', 'huwelijken', 'huwende amsterdammer', 'ijzel',
              'inburgering', 'indexcijfers', 'indicatie geconstateerd', 'indicaties',
              'individueel', 'infectieziekten', 'ingetrokken', 'inkomen', 'inkomsten',
              'innovatie', 'inslagen', 'instroom', 'intensiteit', 'internationaal',
              'internet', 'invalide', 'invalideparkeerplaatsen', 'inwinningsdatum',
              'inzameldag', 'inzameldagen', 'jaap eden', 'jaarcijfers', 'jeugd',
              'jeugd-ggz', 'jeugdgezondheidszorg', 'jeugdzorg', 'jeughdhulpverlening',
              'jongeren', 'jongerenhuisvesting', 'junioren', 'kaart',
              'kaart achter de burgemeester', 'kaartblad', 'kaarttegels',
              'kadastraal object', 'kadastraal perceel', 'kadastraal subject',
              'kadastrale aanduiding', 'kadastrale grens', 'kadastrale grenzen',
              'kadastrale kaart', 'kadastrale kaarten', 'kalender', 'kamers',
              'kansengebieden', 'kansenkaart', 'kantoor', 'kantoorprijzen',
              'kantoren', 'kantorenloods', 'kapvergunning', 'kartografie', 'kassen',
              'kastanje', 'kastanjebloedingsziekte', 'kastanjebomen', 'kasteel',
              'kastelen', 'kavel', 'kavels', 'kbk10', 'kbk50', 'kbka', 'kbka10',
              'kbka50', 'kerk', 'kerken', 'kermis', 'kerncijfers', 'kernregistratie',
              'kernregistratie monumenten', 'kiesgerechtigden', 'kinderboerderij',
              'kinderdagverblijven', 'kinderopvang', 'klasse', 'kleine',
              'kleinschalig', 'kleinschalige', 'kleinschalige topografie',
              'klinieken', 'knnv', 'koopjaar', 'koopjaren', 'koopkrachtbinding',
              'koopsom', 'koopsommen', 'koopwoning', 'kosten', 'koude', 'kruidentuin',
              'kruispunten', 'kunst', 'kunstwerken', 'laadnetwerk', 'laden',
              'laden en lossen', 'landbouw', 'landhuis', 'landhuizen', 'landschap',
              'landsdekkend', 'laseraltimetrie', 'laserpunten', 'layers',
              'leaseautos', 'leef', 'leefbaar', 'leefgebieden', 'leefomgeving',
              'leefomgevingen', 'leefstijl', 'leeftijd', 'leeftijdsgroepen',
              'leegstaande', 'leegstand', 'leerlingen', 'leerplicht', 'leisure',
              'lesbisch', 'levensonderhoud', 'lhbt', 'lichamelijk', 'ligging',
              'ligweide', 'linked', 'literatuur', 'live', 'live uitzendingen',
              'logies', 'logiesvormen', 'logopedie', 'logopedisten', 'loketten',
              'loop van de bevolking', 'lossen', 'luchtaanval', 'luchthaven',
              'luchtkwaliteit', 'luchtmetingen', 'maaiveld', 'maatje',
              'maatschappelijke activiteiten', 'maatschappelijke organisaties',
              'macro-conjunctuur', 'mantelzorg', 'maps', 'markt', 'markten',
              'meetbout', 'meetbouten', 'meldingen', 'meldpunt', 'mensen', 'meta',
              'metadata', 'meteorologie', 'meting', 'metingen', 'metro',
              'metropoolregio', 'middelbare', 'middelbare school',
              'migratieachtergrond', 'milieu', 'milieuzone', 'minima', 'misdrijven',
              'mobiliteit', 'moestuin', 'molen', 'molens', 'monitor', 'monument',
              'monumentaal', 'monumentcomplex', 'monumenten', 'moskee', 'moskees',
              'moties', 'motorvoertuigen', 'musea', 'museum', 'muurplanten',
              'muurvlak', 'muurvlakken', 'muziek', 'nationaliteit', 'nationaliteiten',
              'naturalisatie', 'natuur', 'natuurvoedingswinkels', 'nauwkeurig',
              'nest', 'nesten', 'niet-natuurlijk persoon', 'nieuw', 'nieuw-west',
              'nieuwbouw', 'nieuwkomers', 'noord', 'nulmeting', 'nulpunt',
              'nummeraanduiding', 'nummeraanduidingen', 'oefentherapeut',
              'oefentherapie', 'ois', 'omgeving', 'omgevingen', 'omgevingsschade',
              'omgevingsvergunningen', 'omgevingswet', 'omgewaaid', 'omvalling',
              'omzet', 'ondergrond', 'onderhoud groenvoorzieningen',
              'onderhoud straten-stoepen', 'ondernemersvereniging', 'onderwijs',
              'onderwijsdata', 'onderwijsniveau', 'ongelukken', 'ongevallen',
              'onrechtmatige bewoning', 'ontmoeting', 'ontwikkeling',
              'oorspronkelijk bouwjaar', 'oost', 'opbrekingen', 'opbrengsten', 'open',
              'openbaar', 'openbaar vervoer', 'openbare', 'openbare ruimte',
              'openbare ruimtes', 'ophaaldagen grofvuil', 'ophaaldagen huisvuil',
              'ophalen grofvuil', 'opheffingen', 'oplaadpunten', 'oplaadstations',
              'opladen', 'opleiding', 'opleidingsniveau', 'oppervlakte',
              'oprichtingen', 'opstal', 'opvang', 'opvoeden',
              'opvoedingsondersteuning', 'ordening', 'ordening\n', 'organisaties',
              'orkest', 'oud', 'ouderen', 'ov', 'overgewicht', 'overlast',
              'overnachtingen', 'overzicht', 'pand', 'panden', 'panoramabeeld',
              'panoramabeelden', 'papier', 'park', 'parkeerautomaat',
              'parkeerautomaten', 'parkeerdruk', 'parkeergarages', 'parkeergebieden',
              'parkeerkaarten', 'parkeerplaatsen', 'parkeerplan', 'parkeervakken',
              'parkeervergunning', 'parkeervergunningen', 'parkeerzones', 'parkeren',
              'participatie', 'partnerschappen', 'partycentra', 'partylocatie', 'pc',
              'perceel', 'perceelgrootte', 'perceelnummer', 'percelen', 'personeel',
              'personeelkosten', 'personen', 'persoon', 'persoonlijke', 'plannen',
              'planning', 'plantsoen', 'plantsoenen', 'plastic', 'plekken', 'po',
              'podia', 'politie', 'politiebureau', 'politiek', 'post', 'postcode',
              'postcodes', 'potentie', 'praktijk', 'precies', 'primair', 'processie',
              'processierups', 'producten', 'prognoses', 'projecten',
              'projectontwikkelaars', 'provinciale', 'provincie', 'psychiaters',
              'psychiatrie', 'psychologen', 'psychosociaal', 'psychotherapeuten',
              'publiekrechtrelijke beperkingen', 'puntdichtheid', 'puntenwolk',
              'radar', 'real-time', 'realisatie', 'recht', 'rechten',
              'rechtstoestand', 'rechtszekerheid', 'recreatie', 'rectificatie',
              'reden opvoer', 'redenopvoer', 'referendum', 'referentie',
              'referentiepunt', 'referentiepunten', 'regeling', 'regen', 'register',
              'registerkinderopvang\n', 'registratie meetbouten', 'reisafstand',
              'reistijd', 'reistijden', 'reizen', 'rekening', 'religie',
              'remote sensing', 'restaurant', 'restaurants', 'resultaatrekening',
              'resultaten', 'retributies', 'ride', 'rietland', 'rijden',
              'rijksmonument', 'rijksmonumenten', 'rijksmuseum', 'rollaag',
              'rollagen', 'routes', 'ruimte', 'ruimte\n', 'ruimtelijk\n',
              'ruimtelijke', 'ruimtezoekers', 'rups', 'ruw', 'samen', 'schades',
              'scheidingspercentages', 'schiphol', 'scholen', 'scholier',
              'scholieren', 'school', 'schoolgebouwen', 'schoolverlaters',
              'schoolverzuim', 'schoolwerktuin', 'schoolwijzer', 'schoonhouden',
              'schriftelijke vragen', 'schuldhulpverlening', 'secundair', 'services',
              'shapefile', 'shoppen', 'slachtoffer', 'slachtoffers', 'snelheid',
              'snelle groeiers', 'snelweg', 'snijlijnen', 'so', 'sociaal minimum',
              'sociaal-emotioneel', 'spanningsindicator', 'speciaal',
              'speciaal onderwijs', 'splitsing', 'splitsingsvergunningen', 'sport',
              'sportaccommodaties', 'sportevenement', 'sportevenementen', 'sporthal',
              'sporthallen', 'sportplekken', 'sportverenigingen', 'spuiten', 'staat',
              'stacaravan', 'stacaravans', 'stadsarchief', 'stadsdeel',
              'stadsdeelraad', 'stadsdelen', 'stadsgezicht', 'stadsloods',
              'stadsparken', 'stadspas', 'stadsstrand', 'stallinggedrag',
              'standgegevens', 'starters', 'startersvacatures.', 'startkwalificatie',
              'statistiek', 'statistieken', 'status', 'stedenbouw', 'stembureau',
              'stembureaus', 'stemlocaties', 'stemmen', 'sterfte', 'sterren',
              'stoffen', 'stoplichten', 'storm', 'stort', 'straat', 'straatnaam',
              'straatnamen', 'straatnamenregister', 'straatparkeren', 'straten',
              'streekproducten', 'streetview', 'strooien', 'strooiroutes',
              'structuur', 'studenten', 'studentenhuisvesting', 'studeren', 'stukken',
              'subsidie', 'subsidieregister', 'subsidies', 'subsidies.', 'synagoge',
              'synagoges', 'talent voor de toekomst', 'tandarts', 'tandartspraktijk',
              'tandzorg', 'tariefgebieden', 'tarieven', 'taxi', 'taxistandplaatsen',
              'technologie', 'technologievelden', 'tegels', 'tempel', 'tempels',
              'temperatuur', 'tentoonstellingen', 'terras', 'terreinen',
              'terreinmodel', 'terreinmodellen', 'tertiar', 'textiel', 'theater',
              'thuislozen', 'thuislozenzorg', 'thuiszorg', 'tijd', 'tijdreeks',
              'tiles', 'toegang', 'toegankelijkheid', 'toegevoegde waarde',
              'toerisme', 'toerisme\n', 'toeristen', 'toezicht', 'toneel', 'topo',
              'topografie', 'touringcars', 'trade', 'tram', 'transformatie',
              'transparantie', 'transseksueel', 'tunnels', 'tweede', 'twitter',
              'type woonobject', 'uitgaan', 'uitgaanscentrum', 'uitgave', 'uitgaven',
              'uitkeringen', 'uitslagen', 'uitstroom', 'unesco', 'universiteiten',
              'vacatures', 'vaccinatie', 'veer', 'veiligheid', 'veiligheidsindex',
              'verbeteraspecten buurt', 'verblijfsobject', 'verblijfsobjecten',
              'verbruik', 'verdachten', 'verdedigingswerk', 'verdedigingswerken',
              'verdieping toegang', 'vereniging', 'vergrijzing.', 'vergunning',
              'vergunningen', 'verhuisgeneigdheid', 'verhuizingen', 'verhuringen',
              'verhuur', 'verkeer', 'verkeersexamen', 'verkeerslicht',
              'verkeersongevallen', 'verkeersslachtoffers', 'verkenningen',
              'verkiezing', 'verkiezingen', 'verkiezingsuitslagen',
              'verkochte woningen', 'verkoopprijs', 'verkoopprijzen', 'vermogen',
              'verplaatsingen', 'verpleeghuizen', 'verslaafde', 'verslaafden',
              'verslagen', 'verslavingszorg', 'vertragingen', 'vertrek',
              'vertrektijden', 'vervoer', 'verzorgingshuizen', 'vestiging',
              'vestigingen', 'vestingen', 'videoverslagen', 'vindplaats',
              'vispassage', 'vloeroppervlakte', 'voedselwagens', 'volwassenen',
              'volwasseneneducatie', 'voorschool', 'voorstellingen',
              'voortgezet onderwijs', 'vraag', 'vrachtverkeer', 'vrachtwagens',
              'vrije', 'vrijplaats', 'vrijwilliger', 'vruchtgebruik', 'waardering',
              'wachtlijst', 'wandkaart', 'warmte', 'warmtekoudeopslak', 'water',
              'waterpassing', 'waterschap', 'waterschappen', 'weer',
              'weg- en waterwerken', 'wegen', 'wegenverkeerswet', 'wegverkeer',
              'wegwerkzaamheden', 'welstand', 'welstandsniveau', 'welstandssysteem',
              'welzijn', 'werelderfgoed', 'wereldoorlog', 'werk',
              'werk in uitvoering', 'werkenden', 'werkgelegenheid', 'werkloosheid',
              'werkloosheidscijfers', 'werknemers', 'werkplek', 'werkplekken',
              'werktijd', 'werkzaamheden', 'werkzame', 'werkzame personen', 'west',
              'wetenschappelijk onderwijs', 'wijk', 'wijkagent', 'wijkcentrum',
              'wijken', 'wilde bijen', 'wildrooster', 'wind', 'windenergie',
              'windmolens', 'windrichting', 'windvisie', 'winkelgebied', 'winkeliers',
              'winkeliersverenigingen', 'winkels', 'winkelstraten', 'winter', 'wkpb',
              'wo', 'wonen', 'woning', 'woningbezetting', 'woningbouw',
              'woningdichtheid', 'woningen', 'woningprijs', 'woningtoewijzigingen',
              'woningvoorraad', 'woningwaarde', 'woningzoekenden', 'woonduur',
              'woonhuis', 'woonhuizen', 'woonlasten', 'woonomgeving', 'woonplaats',
              'woonplaatsen', 'wozwaarde', 'ww', 'zakelijk recht',
              'zakelijke dienstverlening', 'zakelijke rechten', 'zakking',
              'zakking cumulatief', 'zakkingssnelheid', 'zeehaven', 'zelfbouw',
              'zelfstandigen', 'zettingsgedrag', 'zomer', 'zomervlucht', 'zon',
              'zonatlas', 'zones', 'zonne-energie', 'zonnepanelen', 'zorg',
              'zorggebruik', 'zorgverleners', 'zuid', 'zuidoost', 'zwaluw', 'zwembad',
              'zwembaden'
              ]
)


CONTACT_POINT = dcat.Object(
    required=True,
    title=""
).add(
    'vcard:fn',
    dcat.PlainTextLine(
        description="Geef de naam van de contactpersoon voor eventuele vragen over de inhoud en kwaliteit van de gegevens.",
        title="Inhoudelijke contactpersoon",
        required=True
    )
).add(
    'vcard:hasEmail',
    dcat.String(
        format='email',
        title="E-mail inhoudelijke contactpersoon"
    )
).add(
    'vcard:hasURL',
    dcat.String(
        format='uri',
        title="Website inhoudelijke contactpersoon",
        # description="Website inhoudelijk contactpersoon"
    )
)


DCT_PUBLISHER = dcat.Object(
    required=True,
    title=""
).add(
    'foaf:name',
    dcat.PlainTextLine(
        title="Technische contactpersoon",
        description="Geef de naam van de contactpersoon voor technische vragen over de aanlevering. Dit kan dezelfde contactpersoon zijn als voor de inhoudelijke vragen.",
        required=True
    )
).add(
    'foaf:mbox',
    dcat.String(
        format='email',
        title="E-mail technische contactpersoon"
        # description="Email technisch contactpersoon"
    )
).add(
    'foaf:homepage',
    dcat.String(
        format='uri',
        title="Website technische contactpersoon"
        # description="Website technisch contactpersoon"
    )
)


CATALOG_RECORD = dcat.Object(
    required=True,
    title=""
).add(
    'dct:issued',
    dcat.Date(
        title="Publicatiedatum",
        description="De datum waarop deze beschrijving van de gegevensset beschikbaar is gesteld",
        default=datetime.date.today().isoformat()
    )
).add(
    'dct:modified',
    dcat.Date(
        title="Wijzigingsdatum",
        description="De datum waarop deze beschrijving van de gegevensset voor het laatst is gewijzigd",
        default=datetime.date.today().isoformat(),
        required=True
    )
)


DISTRIBUTION = dcat.Object().add(
    'dct:title',
    dcat.PlainTextLine(
        title="Titel",
        required=True
    )
).add(
    'dct:description',
    Markdown(
        title="Beschrijving",
    )
).add(
    'dcat:accessURL',
    dcat.String(
        format='uri',
        title="URL",
        description="Link naar de daadwerkelijke gegevensset",
        required=True
    )
).add(
    'dct:issued',
    dcat.Date(
        title="Verversingsdatum",
        description="De datum waarop de inhoud van deze link voor het laatst is geactualiseerd.",
        default=datetime.date.today().isoformat()
    )
).add(
    'ams:resourceType',
    dcat.Enum(
        [
            ('data', "Data"),
            ('doc', "Documentatie"),
            ('vis', "Visualisatie"),
            ('app', "Voorbeeldtoepassing")
        ],
        title="Type resource",
        required=True
    )
).add(
    'ams:distributionType',
    dcat.Enum(
        [
            ('api', "API/Service"),
            ('file', "Bestand"),
            ('web', "Website")
        ],
        title="Verschijningsvorm",
        required=True
    )
).add(
    'ams:layerIdentifier',
    dcat.PlainTextLine(
        title="Interne Kaartlaag ID",
        description="De Citydata kaartlaag waarmee deze dataset op de kaart getoond kan worden"
    )
).add(
    'ams:serviceType',
    dcat.Enum(
        [
            ('atom', "REST: Atom feed"),
            ('rest', "REST: overig"),
            ('csw', "CSW"),
            ('wcs', "WCS"),
            ('wfs', "WFS"),
            ('wms', "WMS"),
            ('wmts', "WMTS"),
            ('soap', "SOAP"),
            ('other', "Anders")
        ],
        title="Type API/Service",
        description="Geef het type API of webservice"
    )
).add(
    'dct:format',
    dcat.Enum(
        [
            ('n/a', ""),
            ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', "xlsx"),
            ('application/pdf', "pdf"),
            ('text/csv', "csv"),
            ('application/json', "json"),
            ('application/vnd.geo+json', "geojson"),
            ('application/zip; format="shp"', "shp"),
            ('application/xml', "xml"),
            ('application/octet-stream', "anders"),
        ],
        title="Type bestand"
    )
).add(
    'ams:classification',
    dcat.Enum(
        [
            ('public', "Publiek toegankelijk"),
        ],
        title="Classification"
    )
).add(
    'dcat:byteSize',
    dcat.Integer(
        minimum=0,
        title="Bestandsgrootte",
        description="Bestandsgrootte in bytes",
        required=True
    )
).add(
    'foaf:isPrimaryTopicOf',
    CATALOG_RECORD
)


DATASET = dcat.Object().add(
    'dct:title',
    dcat.PlainTextLine(
        title="Titel",
        #description="Geef een titel van de gegevensset.",
        required=True
    )
).add(
    'dct:description',
    Markdown(
        title="Beschrijving",
        description="Geef een samenvatting van de inhoud van de gegevensset, welke gegevens zitten erin en wat is expliciet eruit gelaten",
        required=True
    )
).add(
    'dcat:distribution',
    dcat.List(
        DISTRIBUTION,
        title="Resources"
    )
).add(
    'overheidds:doel',
    Markdown(
        title="Doel",
        description="Geef aan met welk doel deze gegevensset is aangelegd. Waarom bestaat deze gegevensset?",
        required=True
    )
).add(
    'dcat:landingPage',
    dcat.String(
        title="URL voor meer informatie (optioneel)",
        format='uri'
    )
).add(
    'dct:accrualPeriodicity',
    dcat.Enum(
        [
            ('unknown', "onbekend"),
            ('realtime', "continu"),
            ('day', "dagelijks"),
            ('2pweek', "twee keer per week"),
            ('week', "wekelijks"),
            ('2weeks', "tweewekelijks"),
            ('month', "maandelijks"),
            ('quarter', "eens per kwartaal"),
            ('2pyear', "halfjaarlijks"),
            ('year', "jaarlijks"),
            ('2years', "tweejaarlijks"),
            ('4years', "vierjaarlijks"),
            ('5years', "vijfjaarlijks"),
            ('10years', "tienjaarlijks"),
            ('reg', "regelmatig"),
            ('irreg', "onregelmatig"),
            ('req', "op afroep"),
            ('other', "anders")
        ],
        title="Wijzigingsfrequentie",
        default='unknown'
        #description="Frequentie waarmee de gegevens worden geactualiseerd"
    )
).add(
    'dct:temporal',
    dcat.Object(
        title=""
        #description="De tijdsperiode die de gegevensset beslaat"
    ).add(
        'time:hasBeginning',
        dcat.Date(
            title="Tijdsperiode van",
            description="Geef de tijdsperiode aan (begindatum), die de gegevensset beslaat."
        )
    ).add(
        'time:hasEnd',
        dcat.Date(
            title="Tijdsperiode tot",
            description="Geef de tijdsperiode aan (einddatum), die de gegevensset beslaat."
        )
    )
).add(
    'ams:temporalUnit',
    dcat.Enum(
        [
            ('na', "Geen tijdseenheid"),
            ('realtime', "Realtime"),
            ('minutes', "Minuten"),
            ('hours', "Uren"),
            ('parttime', "Dagdelen"),
            ('days', "Dagen"),
            ('weeks', "Weken"),
            ('months', "Maanden"),
            ('quarter', "Kwartalen"),
            ('years', "Jaren"),
            ('other', "anders")
        ],
        title="Tijdseenheid"
        #description="Geef de tijdseenheid aan waarin de gegevensset is uitgedrukt, indien van toepassing."
    )
).add(
    'ams:spatialDescription',
    dcat.PlainTextLine(
        title="Omschrijving gebied"
    )
).add(
    'dct:spatial',
    dcat.PlainTextLine(
        title="Coördinaten gebiedskader",
        description="Beschrijving of coördinaten van het gebied dat de gegevensset bestrijkt (boundingbox). Rijksdriehoeksstelsel (pseudo-RD)"
    )
).add(
    'ams:spatialUnit',
    dcat.Enum(
        [
            ('na', "Geen geografie"),
            ('specific', "Specifieke punten/vlakken/lijnen"),
            ('city', "Gemeente"),
            ('district', "Stadsdeel"),
            ('area', "Gebied"),
            ('borrow', "Wijk"),
            ('neighborhood', "Buurt"),
            ('block', "Bouwblok"),
            ('zip4', "Postcode (4 cijfers)"),
            ('zip5', "Postcode (4 cijfers, 1 letter)"),
            ('zip6', "Postcode (4 cijfers, 2 letters)"),
            ('other', "anders")
        ],
        default='na',
        title="Gebiedseenheid"
        #description="Geef een eenheid van het gebied waarin de gegevensset is uitgedrukt."
    )
).add(
    'overheid:grondslag',
    Markdown(
        title="Juridische grondslag",
        description="Geef indien van toepassing aan wat is de oorspronkelijke juridische basis is van de gegevensset."
    )
).add(
    'dct:language',
    LANGUAGE
).add(
    'ams:owner',
    dcat.PlainTextLine(
        title="Eigenaar",
        description="Eigenaar en verantwoordelijke voor de betreffende registratie, ook wel bronhouder genoemd. Bij de overheid is dit het bestuursorgaan of rechtspersoon aan wie bij wettelijk voorschrift de verantwoordelijkheid voor het bijhouden van gegevens in een registratie is opgedragen.",
        examples=[
            'AEB Amsterdam',
            'Amsterdam Economic Board',
            'Amsterdam Marketing',
            'Amsterdam Museum',
            'Athlon Car Lease',
            'Brandweer Amsterdam-Amstelland',
            'CBS',
            'CIBG',
            'Cliëntenbelang',
            'Cultuurcompagnie Noord-Holland',
            'GGD Amsterdam',
            'GOVI',
            'Gemeente Amsterdam',
            'Gemeente Amsterdam, Basisinformatie',
            'Gemeente Amsterdam, Bestuur en Organisatie',
            'Gemeente Amsterdam, Economie',
            'Gemeente Amsterdam, Grond en Ontwikkeling',
            'Gemeente Amsterdam, Monumenten en Archeologie',
            'Gemeente Amsterdam, Onderwijs, Jeugd en Zorg',
            'Gemeente Amsterdam, Onderzoek, Informatie en Statistiek',
            'Gemeente Amsterdam, Projectmanagementbureau',
            'Gemeente Amsterdam, Ruimte en Duurzaamheid',
            'Gemeente Amsterdam, Sport en Bos',
            'Gemeente Amsterdam, Stadsarchief',
            'Gemeente Amsterdam, Stadsdeel Centrum',
            'Gemeente Amsterdam, Stadsdeel West',
            'Gemeente Amsterdam, Verkeer en Openbare Ruimte',
            'Gemeente Amsterdam, Wonen',
            'Gemeente Amsterdam, programma Afval Keten',
            'Gemeente Amsterdam, stadsdeel Zuidoost',
            'JeKuntMeer.nl',
            'KNMI',
            'Kadaster',
            'Landelijk Register Kinderopvang en Peuterspeelzalen',
            'Liander',
            'Ministerie van OCW',
            'Nationale Databank Wegverkeergegevens',
            'Open Cultuur Data',
            'Politie Amsterdam-Amstelland',
            'Rijksdienst voor Cultureel Erfgoed',
            'Rijksdienst voor Ondernemend Nederland',
            'Rijksmuseum Amsterdam',
            'Rijkswaterstaat',
            'UWV',
            'Waag Society'
        ]
    )
).add(
    'dcat:contactPoint',
    CONTACT_POINT
).add(
    'dct:publisher',
    DCT_PUBLISHER
).add(
    'dcat:theme',
    dcat.List(
        THEME,
        title="Thema",
        required=True,
        allow_empty=False,
        unique_items=True
        #description="Geef aan onder welke hoofdthema’s de gegevensset valt."
    ),
).add(
    'dcat:keyword',
    dcat.List(
        KEYWORD,
        title="Tags",
        unique_items=True,
        #description="Geef een aantal trefwoorden, die van toepassing zijn op de gegevensset, zodat de gegevensset gevonden kan worden."
    )
).add(
    'ams:license',
    dcat.Enum(
        [
            ('cc-by', "Creative Commons, Naamsvermelding"),
            ('cc-by-nc', "Creative Commons, Naamsvermelding, Niet-Commercieel"),
            ('cc-by-nc-nd', "Creative Commons, Naamsvermelding, Niet-Commercieel, Geen Afgeleide Werken"),
            ('cc-by-nc-sa', "Creative Commons, Naamsvermelding, Niet-Commercieel, Gelijk Delen"),
            ('cc-by-nd', "Creative Commons, Naamsvermelding, Geen Afgeleide Werken"),
            ('cc-by-sa', "Creative Commons, Naamsvermelding, Gelijk Delen"),
            ('cc-nc', "Creative Commons, Niet-Commercieel"),
            ('cc-zero', "Publiek Domein"),
            ('other-open', "Anders, Open"),
            ('other-by', "Anders, Naamsvermelding"),
            ('other-nc', "Anders, Niet Commercieel"),
            ('other-not-open', "Anders, Niet Open"),
            ('unspec', "Niet gespecificeerd")
        ],
        title="Licentie",
        description="Geef aan onder welke open data licentie de gegevensset gepubliceerd is, indien van toepassing. Gebruik invulhulp om licentie te bepalen. Indien er sprake is van een gedeeltelijk publieke dataset, dan geldt de licentie voor het publieke deel.",
        required=True,
        default='unspec'
    )
).add(
    'dct:identifier',
    dcat.PlainTextLine(
        title="UID",
        description="Unieke identifier"
    )
).add(
    'foaf:isPrimaryTopicOf',
    CATALOG_RECORD
)


# print(json.dumps(
#     DATASET.schema,
#     indent='  ', sort_keys=True
# ))

# print(DATASET.full_text_search_representation({
#     'dct:title': 'my dct:title',
#     'dcat:distribution': [
#         {
#             'dct:description': "de omschrijving van één of andere **resource** met <b>markdown</b> opmaak.",\
#             'dct:license': "cc-by-nc-sa"
#         }
#     ]
# }))
