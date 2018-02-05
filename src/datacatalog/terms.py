from pyld import jsonld

_CONTEXT = {

    # Standard namespaces:
    'foaf': 'http://xmlns.com/foaf/0.1/',
    'skos': 'http://www.w3.org/2004/02/skos/core#',

    # Our namespaces:
    # 'term': 'http://datacatalogus.amsterdam.nl/term/',
    'class': {
        '@id': 'http://datacatalogus.amsterdam.nl/term/classification/',
        '@container': '@set'
    },
    'org': {
        '@id': 'http://datacatalogus.amsterdam.nl/term/organization/',
        '@container': '@set'
    },
    'icons': 'http://datacatalogus.amsterdam.nl/icons/',
    'theme': {
        '@id': 'http://datacatalogus.amsterdam.nl/term/theme/',
        '@container': '@set'
    }
}

TERMS = {
    '@context': {
        'class': {
            '@container': '@set',
            '@id': 'http://datacatalogus.amsterdam.nl/term/classification/'
        },
        'foaf': 'http://xmlns.com/foaf/0.1/',
        'icons': 'http://datacatalogus.amsterdam.nl/icons/',
        'org': {
            '@container': '@set',
            '@id': 'http://datacatalogus.amsterdam.nl/term/organization/'
        },
        'skos': 'http://www.w3.org/2004/02/skos/core#',
        'theme': {
            '@container': '@set',
            '@id': 'http://datacatalogus.amsterdam.nl/term/theme/'
        }
    },
    '@id': 'http://datacatalogus.amsterdam.nl/term/',
    'class': [
        {
            '@id': 'class:open',
            'skos:prefLabel': 'Open Data'
        }
    ],
    'org': [
        {
            '@id': 'org:gemeente-amsterdam-ruimte-en-duurzaamheid',
            'foaf:depiction': 'https://files.datapress.com/amsterdam/wp-uploads/20160216153028/amsterdam.png',
            'foaf:homepage': 'https://www.amsterdam.nl/gemeente/organisatie/ruimte-economie/ruimte-duurzaamheid/ruimte-duurzaamheid/',
            'foaf:name': 'Gemeente Amsterdam, Ruimte en Duurzaamheid',
            'skos:note': 'Ruimte en Duurzaamheid werkt op ieder schaalniveau, van portiek tot\n'
                         'metropool, aan het ontwikkelen van een duurzame visie op de stad\n'
                         'Amsterdam, het uitwerken van die visie tot concrete voorstellen en\n'
                         'inrichtingsplannen en het mogelijk maken van die ontwikkelingen.\n'
                         '\n'
                         '[www.amsterdam.nl/gemeente/organisatie/ruimte-economie/ruimte-duurzaamheid/ruimte-duurzaamheid/](https://www.amsterdam.nl/gemeente/organisatie/ruimte-economie/ruimte-duurzaamheid/ruimte-duurzaamheid/)\n'
        },
        {
            '@id': 'org:gemeente-amsterdam-onderzoek-informatie-en-statistiek',
            'foaf:depiction': 'https://files.datapress.com/amsterdam/wp-uploads/20160216153028/amsterdam.png',
            'foaf:homepage': 'http://www.ois.amsterdam.nl',
            'foaf:name': 'Gemeente Amsterdam, Onderzoek, Informatie en Statistiek',
            'skos:note': '[www.ois.amsterdam.nl](http://www.ois.amsterdam.nl)'
        },
        {
            '@id': 'org:gemeente-amsterdam-monumenten-en-archeologie',
            'foaf:depiction': 'https://files.datapress.com/amsterdam/wp-uploads/20160216153028/amsterdam.png',
            'foaf:homepage': 'https://www.amsterdam.nl/kunstencultuur/monumenten/',
            'foaf:name': 'Gemeente Amsterdam, Monumenten en Archeologie',
            'skos:note': '[www.amsterdam.nl/kunstencultuur/monumenten/](https://www.amsterdam.nl/kunstencultuur/monumenten/)\n'
        },
        {
            '@id': 'org:gemeente-amsterdam-verkeer-en-openbare-ruimte',
            'foaf:depiction': 'https://files.datapress.com/amsterdam/wp-uploads/20160216153028/amsterdam.png',
            'foaf:homepage': 'https://www.amsterdam.nl/gemeente/organisatie/ruimte-economie/verkeer-openbare/',
            'foaf:name': 'Gemeente Amsterdam, Verkeer en Openbare Ruimte',
            'skos:note': 'Verkeer en Openbare Ruimte staat voor de bereikbaarheid, de veiligheid\n'
                         'en de kwaliteit van de openbare ruimte van Amsterdam. Zij werkt aan een\n'
                         'stad die bereikbaar is op alle niveaus: internationaal, nationaal,\n'
                         'regionaal, stedelijk en lokaal.\n'
                         '\n'
                         '[www.amsterdam.nl/gemeente/organisatie/ruimte-economie/verkeer-openbare/](https://www.amsterdam.nl/gemeente/organisatie/ruimte-economie/verkeer-openbare/)\n'
        },
        {
            '@id': 'org:gemeente-amsterdam--basisinformatie',
            'foaf:depiction': 'https://files.datapress.com/amsterdam/wp-uploads/20160216153028/amsterdam.png',
            'foaf:homepage': 'https://www.amsterdam.nl/gemeente/organisatie/dienstverlening/basisinformatie/basisinformatie/',
            'foaf:name': 'Gemeente Amsterdam, Basisinformatie',
            'skos:note': '[www.amsterdam.nl/gemeente/organisatie/dienstverlening/basisinformatie/basisinformatie/](https://www.amsterdam.nl/gemeente/organisatie/dienstverlening/basisinformatie/basisinformatie/)\n'
        },
        {
            '@id': 'org:gemeente-amsterdam-stadsdeel-west',
            'foaf:depiction': 'https://files.datapress.com/amsterdam/wp-uploads/20160216153028/amsterdam.png',
            'foaf:homepage': 'https://www.amsterdam.nl/west',
            'foaf:name': 'Gemeente Amsterdam, Stadsdeel West',
            'skos:note': '[www.amsterdam.nl/west](https://www.amsterdam.nl/west)\n'
        },
        {
            '@id': 'org:amsterdam-marketing',
            'foaf:depiction': 'http://datacatalogus.amsterdam.nl/icons/iamsterdam.png',
            'foaf:homepage': 'http://www.iamsterdam.com',
            'foaf:name': 'Amsterdam Marketing',
            'skos:note': '**Amsterdam Marketing**\\\n[www.iamsterdam.com](http://www.iamsterdam.com)\n'
        },
        {
            '@id': 'org:brandweer-amsterdam-amstelland',
            'foaf:depiction': 'https://files.datapress.com/amsterdam/wp-uploads/20160225144529/brandweer.png',
            'foaf:homepage': 'https://www.brandweer.nl/amsterdam-amstelland',
            'foaf:name': 'Brandweer Amsterdam-Amstelland',
            'skos:note': '[www.brandweer.nl/amsterdam-amstelland](https://www.brandweer.nl/amsterdam-amstelland)\n'
        },
        {
            '@id': 'org:kadaster',
            'foaf:depiction': 'http://datacatalogus.amsterdam.nl/icons/kadaster.png',
            'foaf:homepage': 'http://www.kadaster.nl/',
            'foaf:name': 'Kadaster',
            'skos:note': '**Kadaster**\\\n[www.kadaster.nl](http://www.kadaster.nl/)\n'
        },
        {
            '@id': 'org:cbs',
            'foaf:depiction': 'https://www.cbs.nl/Content/images/cbs-brand.svg',
            'foaf:name': 'CBS',
            'skos:note': 'Het Centraal Bureau voor de Statistiek (CBS) maakt het mogelijk dat\n'
                         'maatschappelijke debatten gevoerd kunnen worden op basis van betrouwbare\n'
                         'statistische informatie. \\_\\_Missie\\_\\_ CBS heeft als taak het\n'
                         'publiceren van betrouwbare en samenhangende statistische informatie, die\n'
                         'inspeelt op de behoefte van de samenleving. Naast de\n'
                         'verantwoordelijkheid voor de nationale (officiële) statistieken is CBS\n'
                         'ook belast met de productie van Europese (communautaire) statistieken.\n'
                         '\\_\\_Werkterrein\\_\\_ De informatie die CBS publiceert, gaat over\n'
                         'onderwerpen die de mensen in Nederland raken. Bijvoorbeeld economische\n'
                         'groei en consumentenprijzen, maar ook criminaliteit en vrije tijd.\n'
        },
        {
            '@id': 'org:ggd-amsterdam',
            'foaf:depiction': 'http://datacatalogus.amsterdam.nl/icons/ggd.png',
            'foaf:homepage': 'http://www.ggd.amsterdam.nl/',
            'foaf:name': 'GGD Amsterdam',
            'skos:note': '**GGD Amsterdam**\\\n[www.ggd.amsterdam.nl](http://www.ggd.amsterdam.nl/)\n'
        },
        {
            '@id': 'org:open-cultuur-data',
            'foaf:depiction': 'https://files.datapress.com/amsterdam/wp-uploads/20160225131113/opencultuurdata.png',
            'foaf:homepage': 'http://www.opencultuurdata.nl',
            'foaf:name': 'Open Cultuur Data',
            'skos:note': '[www.opencultuurdata.nl](http://www.opencultuurdata.nl)\\\n'
                         'Open Cultuur Data is een gezamenlijk initiatief van Kennisland, Open\n'
                         'State Foundation en het Nederlands Instituut voor Beeld en Geluid.\n'
        },
        {
            '@id': 'org:uwv',
            'foaf:depiction': 'https://www.uwv.nl/overuwv/include/images/og_icon.png',
            'foaf:name': 'UWV',
            'skos:note': 'Het UWV staat voor Uitvoeringsinstituut Werknemersverzekeringen, en is\n'
                         'een overheidsinstelling die belast is met de uitvoering van alle\n'
                         'werknemersverzekeringen. Hieronder vallen onder andere de WW, WAO, WIA\n'
                         'en de Ziektewet. In 2002 ontstond het UWV door de samenvoeging van een\n'
                         'aantal instanties\n'
        },
        {
            '@id': 'org:jekuntmeer-nl',
            'foaf:depiction': 'http://datacatalogus.amsterdam.nl/icons/jekuntmeer.png',
            'foaf:homepage': 'https://www.jekuntmeer.nl/',
            'foaf:name': 'JeKuntMeer.nl',
            'skos:note': '**JeKuntMeer.nl**\\\n[www.jekuntmeer.nl](https://www.jekuntmeer.nl/)\n'
        },
        {
            '@id': 'org:knmi',
            'foaf:depiction': 'https://files.datapress.com/wp-content/uploads/sites/2/20161110110057/knmi.png',
            'foaf:homepage': 'www.knmi.nl',
            'foaf:name': 'KNMI',
            'skos:note': 'Het weer is grillig, de bodem beweegt en het klimaat verandert. Voor\n'
                         "onze veiligheid en welvaart moeten we weten welke risico's en kansen dit\n"
                         'oplevert. En: hoe we ons het beste kunnen voorbereiden. Die kennis heeft\n'
                         'het KNMI in huis als het nationale kennis- en datacentrum voor weer,\n'
                         'klimaat en seismologie. Betrouwbaar, onafhankelijk en gericht op wat\n'
                         'Nederland nodig heeft.\\\n'
                         '**[www.knmi.nl](www.knmi.nl)**\n'
        },
        {
            '@id': 'org:gemeente-amsterdam-stadsdeel-centrum',
            'foaf:depiction': 'https://files.datapress.com/amsterdam/wp-uploads/20160216153028/amsterdam.png',
            'foaf:homepage': 'http://www.amsterdam.nl/centrum',
            'foaf:name': 'Gemeente Amsterdam, Stadsdeel Centrum',
            'skos:note': '[www.amsterdam.nl/centrum](http://www.amsterdam.nl/centrum)\n'
        },
        {
            '@id': 'org:gemeente-amsterdam',
            'foaf:depiction': 'https://files.datapress.com/amsterdam/wp-uploads/20160216153028/amsterdam.png',
            'foaf:name': 'Gemeente Amsterdam',
            'skos:note': '\n'
        },
        {
            '@id': 'org:amsterdam-economic-board',
            'foaf:depiction': '2017-09-06-074450.631386HMijn-documentenProjectenDataLabLeefstijlenlogo.png',
            'foaf:name': 'Amsterdam Economic Board',
            'skos:note': 'Het doel is een slimme, gezonde en groene regio. De route daarnaartoe is\n'
                         'in een snel veranderende wereld niet te voorspellen. De Board brengt\n'
                         'onzekerheden en transities in kaart om hier als regio flexibel op in te\n'
                         'kunnen spelen. Samen werken we aan de Metropool van de toekomst door bij\n'
                         'te dragen aan vijf grootstedelijke uitdagingen. Voor elke uitdaging\n'
                         'hebben we een stip aan de horizon geformuleerd. Daar willen we als MRA\n'
                         'staan in 2025: \\_\\_-- Circulaire Economie:\\_\\_ in 2025 is de\n'
                         'Metropoolregio Amsterdam koploper op het gebied van slimme oplossingen\n'
                         'voor het behoud van grondstoffen waardoor waardevolle grondstoffen\n'
                         'steeds langer en efficiënter worden gebruikt. \\_\\_-- Digitale\n'
                         'Connectiviteit:\\_\\_ in 2025 is de Metropoolregio Amsterdam de\n'
                         'belangrijkste plek in Europa voor data-gedreven innovatie. \\_\\_--\n'
                         'Gezondheid:\\_\\_ in 2025 hebben bewoners in de Metropoolregio Amsterdam\n'
                         'twee gezonde levensjaren extra. \\_\\_-- Mobiliteit:\\_\\_ in 2025 is het\n'
                         'stedelijk vervoer in de Metropoolregio Amsterdam emissievrij. \\_\\_--\n'
                         'Talent voor de Toekomst:\\_\\_ in 2025 is de Metropoolregio Amsterdam de\n'
                         'succesvolste regio op het gebied van het benutten, behouden en\n'
                         'aantrekken van talent. Door het initiëren, mobiliseren en vooruitbrengen\n'
                         'van nieuwe initiatieven binnen die uitdagingen en de focus op innovatie\n'
                         'werken we toe naar de Metropool van de toekomst.\n'
        },
        {
            '@id': 'org:gemeente-amsterdam-stadsarchief',
            'foaf:depiction': 'https://files.datapress.com/amsterdam/wp-uploads/20160216153028/amsterdam.png',
            'foaf:homepage': 'https://www.amsterdam.nl/stadsarchief/',
            'foaf:name': 'Gemeente Amsterdam, Stadsarchief',
            'skos:note': 'Het Stadsarchief Amsterdam is het historisch documentatie- centrum van\n'
                         'de stad Amsterdam met 50 kilometer archieven, een historisch-\n'
                         'topografische collectie met miljoenen kaarten, tekeningen, en prenten,\n'
                         'een bibliotheek en omvangrijke geluids-, film- en fotoarchieven.\\\n'
                         '\\\n'
                         '[www.amsterdam.nl/stadsarchief/](https://www.amsterdam.nl/stadsarchief/)\n'
        },
        {
            '@id': 'org:ministerie-van-ocw',
            'foaf:depiction': 'http://datacatalogus.amsterdam.nl/icons/minocw.png',
            'foaf:homepage': 'https://www.rijksoverheid.nl/ministeries/ministerie-van-onderwijs-cultuur-en-wetenschap',
            'foaf:name': 'Ministerie van OCW',
            'skos:note': '**Ministerie van OCW**\\\n'
                         '[www.rijksoverheid.nl/ministeries/ministerie-van-onderwijs-cultuur-en-wetenschap](https://www.rijksoverheid.nl/ministeries/ministerie-van-onderwijs-cultuur-en-wetenschap)\n'
        },
        {
            '@id': 'org:rijkswaterstaat',
            'foaf:depiction': 'https://files.datapress.com/wp-content/uploads/sites/2/20161107134908/rijkswaterstaat.png',
            'foaf:name': 'Rijkswaterstaat',
            'skos:note': 'Samen werken aan een veilig, leefbaar en bereikbaar Nederland. Dat is\nRijkswaterstaat.\n'
        },
        {
            '@id': 'org:gemeente-amsterdam-bestuur-en-organisatie',
            'foaf:depiction': '2017-02-02-145441.884305amsterdam.png',
            'foaf:name': 'Gemeente Amsterdam, Bestuur en Organisatie',
            'skos:note': '\n'
        },
        {
            '@id': 'org:gemeente-amsterdam-grond-en-ontwikkeling',
            'foaf:depiction': 'https://files.datapress.com/amsterdam/wp-uploads/20160216153028/amsterdam.png',
            'foaf:homepage': 'https://www.amsterdam.nl/gemeente/organisatie/ruimte-economie/grond-ontwikkeling-0/',
            'foaf:name': 'Gemeente Amsterdam, Grond en Ontwikkeling',
            'skos:note': '[www.amsterdam.nl/gemeente/organisatie/ruimte-economie/grond-ontwikkeling-0/](https://www.amsterdam.nl/gemeente/organisatie/ruimte-economie/grond-ontwikkeling-0/)\n'
        },
        {
            '@id': 'org:cibg',
            'foaf:depiction': 'http://datacatalogus.amsterdam.nl/icons/cibg.png',
            'foaf:homepage': 'https://www.cibg.nl/',
            'foaf:name': 'CIBG',
            'skos:note': '**CIBG**\\\n[www.cibg.nl](https://www.cibg.nl/)\n'
        },
        {
            '@id': 'org:gemeente-amsterdam-economische-zaken',
            'foaf:depiction': 'https://files.datapress.com/amsterdam/wp-uploads/20160216153028/amsterdam.png',
            'foaf:homepage': 'https://www.amsterdam.nl/gemeente/organisatie/ruimte-economie/economie/economie/',
            'foaf:name': 'Gemeente Amsterdam, Economie',
            'skos:note': '[www.amsterdam.nl/gemeente/organisatie/ruimte-economie/economie/economie/](https://www.amsterdam.nl/gemeente/organisatie/ruimte-economie/economie/economie/)\n'
        },
        {
            '@id': 'org:athlon-car-lease',
            'foaf:depiction': 'http://datacatalogus.amsterdam.nl/icons/athlon.png',
            'foaf:homepage': 'http://www.athlon.com',
            'foaf:name': 'Athlon Car Lease',
            'skos:note': '**Athlon Car Lease**\\\n[www.athlon.com](http://www.athlon.com)\n'
        },
        {
            '@id': 'org:gemeente-amsterdam-onderwijs-jeugd-en-zorg',
            'foaf:depiction': 'https://files.datapress.com/amsterdam/wp-uploads/20160216153028/amsterdam.png',
            'foaf:homepage': 'https://www.amsterdam.nl/gemeente/organisatie/sociaal/onderwijs-jeugd-zorg/',
            'foaf:name': 'Gemeente Amsterdam, Onderwijs, Jeugd en Zorg',
            'skos:note': '[www.amsterdam.nl/gemeente/organisatie/sociaal/onderwijs-jeugd-zorg/](https://www.amsterdam.nl/gemeente/organisatie/sociaal/onderwijs-jeugd-zorg/)\n'
        },
        {
            '@id': 'org:rijksdienst-voor-cultureel-erfgoed',
            'foaf:depiction': 'http://datacatalogus.amsterdam.nl/icons/erfgoed.png',
            'foaf:homepage': 'http://cultureelerfgoed.nl/',
            'foaf:name': 'Rijksdienst voor Cultureel Erfgoed',
            'skos:note': '**Rijksdienst voor Cultureel Erfgoed**\\\n[cultureelerfgoed.nl](http://cultureelerfgoed.nl/)\n'
        },
        {
            '@id': 'org:gemeente-amsterdam-sport-en-bos',
            'foaf:depiction': 'https://files.datapress.com/amsterdam/wp-uploads/20160216153028/amsterdam.png',
            'foaf:homepage': 'https://www.amsterdam.nl/gemeente/organisatie/sociaal/sport-bos/',
            'foaf:name': 'Gemeente Amsterdam, Sport en Bos',
            'skos:note': 'Sport en Bos (mede) organiseert sportevenementen, acquireert\n'
                         'topevenementen, is verantwoordelijk voor de faciliteiten voor breedte-\n'
                         'en topsport. Verder exploiteert en onderhoudt Sport en Bos de\n'
                         'Sporthallen Zuid en het Amsterdamse Bos.\\\n'
                         '\\\n'
                         '[www.amsterdam.nl/gemeente/organisatie/sociaal/sport-bos/](https://www.amsterdam.nl/gemeente/organisatie/sociaal/sport-bos/)\n'
        },
        {
            '@id': 'org:gemeente-amsterdam-projectmanagementbureau',
            'foaf:depiction': 'https://files.datapress.com/amsterdam/wp-uploads/20160216153028/amsterdam.png',
            'foaf:homepage': 'https://www.amsterdam.nl/pmb/',
            'foaf:name': 'Gemeente Amsterdam, Projectmanagementbureau',
            'skos:note': '[www.amsterdam.nl/pmb/](https://www.amsterdam.nl/pmb/)\n'
        },
        {
            '@id': 'org:politie-amsterdam-amstelland',
            'foaf:depiction': 'http://datacatalogus.amsterdam.nl/icons/politie.png',
            'foaf:homepage': 'https://www.politie.nl/',
            'foaf:name': 'Politie Amsterdam-Amstelland',
            'skos:note': '**Politie Amsterdam-Amstelland**\\\n[www.politie.nl](https://www.politie.nl/)\n'
        },
        {
            '@id': 'org:programma-afval-keten',
            'foaf:depiction': '',
            'foaf:name': 'Gemeente Amsterdam, programma Afval Keten ',
            'skos:note': '\n'
        },
        {
            '@id': 'org:nationale-databank-wegverkeergegevens',
            'foaf:depiction': 'http://datacatalogus.amsterdam.nl/icons/ndw.png',
            'foaf:homepage': 'http://ndw.nu/',
            'foaf:name': 'Nationale Databank Wegverkeergegevens',
            'skos:note': '**Nationale Databank Wegverkeergegevens**\\\n[ndw.nu](http://ndw.nu/)\n'
        },
        {
            '@id': 'org:clientenbelang',
            'foaf:depiction': 'https://files.datapress.com/amsterdam/wp-uploads/20160428152048/clientenbelang.png',
            'foaf:homepage': 'http://www.clientenbelangamsterdam.nl/',
            'foaf:name': 'Cliëntenbelang',
            'skos:note': 'Cliëntenbelang Amsterdam is een onafhankelijke belangenbehartiger met\n'
                         'een duidelijk doel: de kwaliteit van leven verbeteren van mensen met een\n'
                         'psychische, lichamelijk of verstandelijke beperking, chronisch zieken,\n'
                         'kwetsbare ouderen en mantelzorgers.\n'
                         '**[www.clientenbelangamsterdam.nl](http://www.clientenbelangamsterdam.nl/)**\n'
        },
        {
            '@id': 'org:waag-society',
            'foaf:depiction': 'http://datacatalogus.amsterdam.nl/icons/waag.png',
            'foaf:homepage': 'http://waag.org/',
            'foaf:name': 'Waag Society',
            'skos:note': '**Waag Society**\\\n[waag.org](http://waag.org/)\n'
        },
        {
            '@id': 'org:landelijk-register-kinderopvang-en-peuterspeelzalen',
            'foaf:depiction': 'http://datacatalogus.amsterdam.nl/icons/rijksoverheid.png',
            'foaf:homepage': 'http://www.landelijkregisterkinderopvang.nl/',
            'foaf:name': 'Landelijk Register Kinderopvang en Peuterspeelzalen',
            'skos:note': '**Landelijk Register Kinderopvang en Peuterspeelzalen**\\\n'
                         '[www.landelijkregisterkinderopvang.nl](http://www.landelijkregisterkinderopvang.nl/)\n'
        },
        {
            '@id': 'org:liander',
            'foaf:depiction': 'http://datacatalogus.amsterdam.nl/icons/liander.png',
            'foaf:homepage': 'https://www.liander.nl/',
            'foaf:name': 'Liander',
            'skos:note': '**Liander**\\\n[www.liander.nl](https://www.liander.nl/)\n'
        },
        {
            '@id': 'org:amsterdam-museum',
            'foaf:depiction': 'http://datacatalogus.amsterdam.nl/icons/amsterdammuseum.png',
            'foaf:homepage': 'http://www.amsterdammuseum.nl',
            'foaf:name': 'Amsterdam Museum',
            'skos:note': '**Amsterdam Museum**\\\n[www.amsterdammuseum.nl](http://www.amsterdammuseum.nl)\n'
        },
        {
            '@id': 'org:rijksdienst-voor-ondernemend-nederland',
            'foaf:depiction': 'https://www.rvo.nl/sites/all/themes/custom/agnl_theme/logos/logo-nl.png',
            'foaf:name': 'Rijksdienst voor Ondernemend Nederland',
            'skos:note': 'De Rijksdienst voor Ondernemend Nederland stimuleert ondernemend\n'
                         'Nederland bij duurzaam, agrarisch, innovatief en internationaal\n'
                         'ondernemen. Met subsidies, het vinden van zakenpartners, kennis en het\n'
                         'voldoen aan wet- en regelgeving. RVO.nl is onderdeel van het ministerie\n'
                         'van Economische Zaken, maar voert ook opdrachten uit namens andere\n'
                         'ministeries, waaronder de ministeries van Buitenlandse Zaken en\n'
                         'Binnenlandse Zaken en Koninkrijkrelaties. Daarnaast werkt RVO.nl in\n'
                         'opdracht van de Europese Unie.\n'
        },
        {
            '@id': 'org:gemeente-amsterdam-stadsdeel-zuidoost',
            'foaf:depiction': 'https://api.datapunt.amsterdam.nl/catalogus/uploads/group/2017-02-02-145441.884305amsterdam.png',
            'foaf:name': 'Gemeente Amsterdam, stadsdeel Zuidoost',
            'skos:note': '\n'
        },
        {
            '@id': 'org:aeb-amsterdam',
            'foaf:depiction': '2017-02-07-161624.851829aeb.png',
            'foaf:homepage': 'http://www.aebamsterdam.nl/',
            'foaf:name': 'AEB Amsterdam',
            'skos:note': '**Afval- en Energiebedrijf Amsterdam**\\\n[www.aebamsterdam.nl](http://www.aebamsterdam.nl/)\n'
        },
        {
            '@id': 'org:rijksmuseum-amsterdam',
            'foaf:depiction': 'http://datacatalogus.amsterdam.nl/icons/rijksmuseum.png',
            'foaf:homepage': 'https://www.rijksmuseum.nl/',
            'foaf:name': 'Rijksmuseum Amsterdam',
            'skos:note': '**Rijksmuseum Amsterdam**\\\n[www.rijksmuseum.nl](https://www.rijksmuseum.nl/)\n'
        },
        {
            '@id': 'org:cultuurcompagnie-noord-holland',
            'foaf:depiction': 'http://datacatalogus.amsterdam.nl/icons/uitinnh.png',
            'foaf:homepage': 'http://www.uitinnoordholland.nl/',
            'foaf:name': 'Cultuurcompagnie Noord-Holland',
            'skos:note': '**Cultuurcompagnie Noord-Holland**\\\n[www.uitinnoordholland.nl](http://www.uitinnoordholland.nl/)\n'
        },
        {
            '@id': 'org:gemeente-amsterdam-wonen',
            'foaf:depiction': 'https://files.datapress.com/amsterdam/wp-uploads/20160216153028/amsterdam.png',
            'foaf:homepage': 'https://www.amsterdam.nl/gemeente/organisatie/ruimte-economie/wonen/',
            'foaf:name': 'Gemeente Amsterdam, Wonen',
            'skos:note': '[www.amsterdam.nl/gemeente/organisatie/ruimte-economie/wonen/](https://www.amsterdam.nl/gemeente/organisatie/ruimte-economie/wonen/)\n'
        },
        {
            '@id': 'org:govi',
            'foaf:depiction': 'http://datacatalogus.amsterdam.nl/icons/govi.png',
            'foaf:homepage': 'http://govi.nu/',
            'foaf:name': 'GOVI',
            'skos:note': '**GOVI**\\\n[govi.nu](http://govi.nu/)\n'
        }
    ],
    'theme': [
        {
            '@id': 'theme:bestuur-en-organisatie',
            'skos:prefLabel': 'Bestuur en organisatie'
        },
        {
            '@id': 'theme:bevolking',
            'skos:prefLabel': 'Bevolking'
        },
        {
            '@id': 'theme:dienstverlening',
            'skos:prefLabel': 'Dienstverlening'
        },
        {
            '@id': 'theme:economie-haven',
            'skos:prefLabel': 'Economie & Haven'
        },
        {
            '@id': 'theme:educatie-jeugd-diversiteit',
            'skos:prefLabel': 'Educatie, Jeugd & Diversiteit'
        },
        {
            '@id': 'theme:energie',
            'skos:prefLabel': 'Energie'
        },
        {
            '@id': 'theme:geografie',
            'skos:prefLabel': 'Geografie'
        },
        {
            '@id': 'theme:milieu-water',
            'skos:prefLabel': 'Milieu & Water'
        },
        {
            '@id': 'theme:openbare-orde-veiligheid',
            'skos:prefLabel': 'Openbare orde & veiligheid'
        },
        {
            '@id': 'theme:openbare-ruimte-groen',
            'skos:prefLabel': 'Openbare ruimte & groen'
        },
        {
            '@id': 'theme:sport-recreatie',
            'skos:prefLabel': 'Sport & recreatie'
        },
        {
            '@id': 'theme:stedelijke-ontwikkeling',
            'skos:prefLabel': 'Stedelijke ontwikkeling'
        },
        {
            '@id': 'theme:toerisme-cultuur',
            'skos:prefLabel': 'Toerisme & cultuur'
        },
        {
            '@id': 'theme:verkeer-infrastructuur',
            'skos:prefLabel': 'Verkeer & Infrastructuur'
        },
        {
            '@id': 'theme:verkiezingen',
            'skos:prefLabel': 'Verkiezingen'
        },
        {
            '@id': 'theme:werk-inkomen',
            'skos:prefLabel': 'Werk & Inkomen'
        },
        {
            '@id': 'theme:wonen-leefomgeving',
            'skos:prefLabel': 'Wonen & leefomgeving'
        },
        {
            '@id': 'theme:zorg-welzijn',
            'skos:prefLabel': 'Zorg & welzijn'
        }
    ]
}

TERMS = jsonld.compact(jsonld.expand(TERMS), _CONTEXT)
#pprint.pprint(TERMS, width=160)
#print(len(TERMS['org']))
