"""
Athena SCIP - Data Quality Module
Improves event data quality through enrichment, filtering, and classification
"""
import re
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ============================================
# SUPPLY CHAIN KEYWORDS - EXPANDED
# ============================================
SUPPLY_CHAIN_KEYWORDS = [
    # Logistics & Transportation
    'ship', 'port', 'container', 'freight', 'cargo', 'vessel', 'tanker',
    'rail', 'truck', 'warehouse', 'inventory', 'distribution', 'logistics',
    'shipping', 'harbor', 'dock', 'terminal', 'conveyor', 'pipeline',
    
    # Manufacturing
    'production', 'factory', 'plant', 'assembly', 'manufacturing',
    'semiconductor', 'chip', 'auto', 'automotive', 'steel', 'smelting',
    'refinery', 'chemical', 'processing', 'fabrication', 'assembly line',
    
    # Raw Materials
    'oil', 'gas', 'wheat', 'corn', 'soy', 'copper', 'aluminum',
    'lithium', 'nickel', 'iron ore', 'rare earth', 'commodity',
    'minerals', 'metals', 'timber', 'lumber', 'cotton', 'rubber',
    
    # Supply Chain Disruptions
    'shortage', 'surplus', 'disruption', 'delay', 'backlog',
    'bottleneck', 'strike', 'sanctions', 'embargo', 'tariff',
    'quota', 'restriction', 'ban', 'blockade', 'closure',
    
    # Geopolitical (Supply Chain Relevant)
    'canal', 'strait', 'blockade', 'border', 'customs', 'quarantine',
    'embargo', 'trade war', 'tariff war', 'export ban', 'import ban',
    
    # Natural Events Affecting Supply Chain
    'earthquake', 'flood', 'hurricane', 'typhoon', 'cyclone', 
    'wildfire', 'drought', 'tsunami', 'storm', 'landslide',
    
    # Accidents & Incidents
    'accident', 'explosion', 'fire', 'collapse', 'derailment',
    'chemical spill', 'oil spill', 'contamination', 'recall',
    'malfunction', 'breakdown', 'failure', 'crash',
    
    # Economic & Business
    'bankruptcy', 'closure', 'insolvency', 'layoff', 'shutdown',
    'merger', 'acquisition', 'buyout', 'divestment',
]

# ============================================
# LOCATION ENRICHMENT - EXPANDED
# ============================================
# ============================================
# LOCATION ENRICHMENT - EXPANDED
# ============================================
LOCATION_KEYWORDS = {
    # Americas
    'USA': ['usa', 'united states', 'america', 'washington', 'new york', 'california', 'texas', 'florida', 'illinois', 'pennsylvania', 'ohio', 'georgia', 'north carolina', 'michigan', 'new jersey', 'virginia', 'washington state', 'arizona', 'massachusetts', 'tennessee', 'indiana', 'missouri', 'maryland', 'wisconsin', 'colorado', 'minnesota', 'south carolina', 'alabama', 'louisiana', 'kentucky', 'oregon', 'oklahoma', 'connecticut', 'puerto rico', 'iowa', 'utah', 'nevada', 'arkansas', 'mississippi', 'kansas', 'new mexico', 'nebraska', 'west virginia', 'idaho', 'hawaii', 'new hampshire', 'maine', 'montana', 'rhode island', 'delaware', 'south dakota', 'north dakota', 'alaska', 'dc', 'vermont', 'wyoming'],
    
    'Canada': ['canada', 'toronto', 'vancouver', 'montreal', 'calgary', 'ottawa', 'edmonton', 'quebec', 'winnipeg', 'halifax'],
    
    'Mexico': ['mexico', 'mexico city', 'monterrey', 'guadalajara', 'puebla', 'tijuana', 'ciudad juarez', 'leon'],
    
    'Brazil': ['brazil', 'brasilia', 'sao paulo', 'rio de janeiro', 'belo horizonte', 'salvador', 'fortaleza', 'curitiba', 'manaus', 'recife', 'porto alegre'],
    
    'Argentina': ['argentina', 'buenos aires', 'cordoba', 'rosario', 'mendoza', 'la plata'],
    
    'Colombia': ['colombia', 'bogota', 'medellin', 'cali', 'barranquilla', 'cartagena'],
    
    'Chile': ['chile', 'santiago', 'valparaiso', 'concepcion', 'antofagasta'],
    
    'Peru': ['peru', 'lima', 'arequipa', 'trujillo', 'callao'],
    
    'Venezuela': ['venezuela', 'caracas', 'maracaibo', 'valencia', 'barquisimeto', 'ciudad guayana', 'maturin', 'bocono'],
    
    # Europe
    'UK': ['uk', 'united kingdom', 'britain', 'england', 'scotland', 'wales', 'northern ireland', 'london', 'manchester', 'birmingham', 'leeds', 'glasgow', 'sheffield', 'bradford', 'edinburgh', 'liverpool', 'bristol', 'cardiff', 'belfast', 'nottingham', 'newcastle'],
    
    'Germany': ['germany', 'berlin', 'munich', 'hamburg', 'cologne', 'frankfurt', 'stuttgart', 'dusseldorf', 'dortmund', 'essen', 'leipzig', 'dresden', 'nuremberg', 'hanover'],
    
    'France': ['france', 'paris', 'marseille', 'lyon', 'toulouse', 'nice', 'nantes', 'strasbourg', 'montpellier', 'bordeaux', 'lille', 'rennes', 'reims', 'le havre', 'saint-etienne'],
    
    'Italy': ['italy', 'rome', 'milan', 'naples', 'turin', 'palermo', 'genoa', 'bologna', 'florence', 'venice', 'verona', 'messina', 'trieste'],
    
    'Spain': ['spain', 'madrid', 'barcelona', 'valencia', 'seville', 'zaragoza', 'malaga', 'murcia', 'palma', 'bilbao', 'alicante', 'cordoba', 'valladolid', 'vigo', 'gijon'],
    
    'Netherlands': ['netherlands', 'amsterdam', 'rotterdam', 'the hague', 'utrecht', 'eindhoven', 'tilburg', 'groningen', 'almere', 'breda'],
    
    'Belgium': ['belgium', 'brussels', 'antwerp', 'ghent', 'charleroi', 'liege', 'bruges', 'namur'],
    
    'Switzerland': ['switzerland', 'zurich', 'geneva', 'basel', 'bern', 'lausanne', 'winterthur', 'st gallen'],
    
    'Austria': ['austria', 'vienna', 'graz', 'linz', 'salzburg', 'innsbruck', 'klagenfurt'],
    
    'Sweden': ['sweden', 'stockholm', 'gothenburg', 'malmo', 'uppsala', 'vasteras', 'orebro', 'linkoping', 'helsingborg'],
    
    'Norway': ['norway', 'oslo', 'bergen', 'trondheim', 'stavanger', 'drammen', 'fredrikstad', 'kristiansand'],
    
    'Denmark': ['denmark', 'copenhagen', 'aarhus', 'odense', 'aalborg', 'esbjerg', 'randers'],
    
    'Finland': ['finland', 'helsinki', 'espoo', 'tampere', 'vantaa', 'oulu', 'turku', 'jyvaskyla', 'lahti'],
    
    'Poland': ['poland', 'warsaw', 'krakow', 'lodz', 'wroclaw', 'poznan', 'gdansk', 'szczecin', 'bydgoszcz', 'lublin', 'katowice', 'bialystok', 'gdynia', 'czestochowa', 'radom'],
    
    'Czech Republic': ['czech', 'czech republic', 'prague', 'brno', 'ostrava', 'plzen', 'liberec', 'olomouc', 'ceske budejovice', 'hradec kralove'],
    
    'Greece': ['greece', 'athens', 'thessaloniki', 'patras', 'iraklion', 'larissa', 'volos', 'rhodes', 'chania', 'ioannina'],
    
    'Portugal': ['portugal', 'lisbon', 'porto', 'braga', 'coimbra', 'setubal', 'funchal', 'aveiro', 'evora'],
    
    'Ireland': ['ireland', 'dublin', 'cork', 'limerick', 'galway', 'waterford', 'drogheda', 'dundalk'],
    
    'Hungary': ['hungary', 'budapest', 'debrecen', 'szeged', 'miskolc', 'pecs', 'gyor', 'nyiregyhaza', 'kecskemet', 'szekesfehervar'],
    
    'Romania': ['romania', 'bucharest', 'cluj-napoca', 'timisoara', 'iasi', 'constanta', 'craiova', 'brasov', 'galati', 'pitesti'],
    
    'Bulgaria': ['bulgaria', 'sofia', 'plovdiv', 'varna', 'burgas', 'russe', 'stara zagora', 'pleven', 'sliven'],
    
    'Croatia': ['croatia', 'zagreb', 'split', 'rijeka', 'osijek', 'zadar', 'velika gorica', 'pula', 'sibenik'],
    
    'Serbia': ['serbia', 'belgrade', 'novi sad', 'nis', 'kragujevac', 'subotica', 'zrenjanin', 'pancevo', 'cacak'],
    
    # Asia
    'China': ['china', 'beijing', 'shanghai', 'guangzhou', 'shenzhen', 'tianjin', 'chengdu', 'chongqing', 'dongguan', 'wuhan', 'hangzhou', 'ningbo', 'qingdao', 'suzhou', 'shijiazhuang', 'foshan', 'nanjing', 'shenyang', 'xian', 'dalian', 'changsha', 'zhengzhou', 'fuzhou', 'quanzhou', 'kunming', 'xiamen', 'wenzhou', 'changchun', 'hefei', 'shanwei', 'lanzhou'],
    
    'India': ['india', 'mumbai', 'delhi', 'bangalore', 'chennai', 'kolkata', 'hyderabad', 'ahmedabad', 'pune', 'surat', 'jaipur', 'lucknow', 'kanpur', 'nagpur', 'indore', 'thane', 'bhopal', 'visakhapatnam', 'patna', 'vadodara', 'coimbatore', 'agra', 'nashik', 'raipur', 'meerut', 'jabalpur', 'varanasi', 'srinagar', 'aurangabad', 'dhanbad'],
    
    'Japan': ['japan', 'tokyo', 'osaka', 'nagoya', 'yokohama', 'sapporo', 'fukuoka', 'kobe', 'kyoto', 'kawasaki', 'hiroshima', 'sendai', 'chiba', 'kitakyushu', 'sakai', 'niigata', 'hamamatsu', 'kumamoto', 'okayama', 'shizuoka', 'sagamihara', 'yokosuka', 'matsuyama', 'kagoshima', 'akita', 'aomori'],
    
    'South Korea': ['south korea', 'korea', 'seoul', 'busan', 'incheon', 'daegu', 'daejeon', 'gwangju', 'suwon', 'ulsan', 'changwon', 'seongnam', 'cheongju', 'jeonju', 'asans', 'ansan', 'gunpo', 'jeju'],
    
    'Indonesia': ['indonesia', 'jakarta', 'surabaya', 'bandung', 'medan', 'semarang', 'palembang', 'makassar', 'depok', 'pekanbaru', 'bekasi', 'tangerang', 'malang', 'padang', 'bali', 'sumatra', 'java', 'kalimantan', 'sulawesi', 'papua', 'palu'],
    
    'Philippines': ['philippines', 'manila', 'cebu', 'davao', 'quezon city', 'caloocan', 'zamboanga', 'taguig', 'pasig', 'valenzuela', 'mandaluyong', 'paranaque', 'las pinas', 'makati', 'marikina', 'muntinlupa', 'batangas', 'cagayan de oro', 'iloilo', 'bacolod', 'general santos', 'kabalalan'],
    
    'Vietnam': ['vietnam', 'ho chi minh', 'hanoi', 'haiphong', 'da nang', 'can tho', 'bien hoa', 'nha trang', 'thanh hoa', 'buon ma thuot', 'hai duong', 'quy nhon', 'vung tau', 'long xuyen', 'my tho', 'cam ranh'],
    
    'Thailand': ['thailand', 'bangkok', 'chonburi', 'chiang mai', 'rayong', 'hat yai', 'phuket', 'samut prakan', 'khon kaen', 'pathum thani', 'nakhon ratchasima', 'nonthaburi', 'udon thani', 'saraburi', 'pattaya'],
    
    'Malaysia': ['malaysia', 'kuala lumpur', 'sepang', 'petaling jaya', 'shah alam', 'subang jaya', 'klang', 'johor bahru', 'george town', 'ipoh', 'kuching', 'kotakinabalu', 'malacca', 'penang', 'sarawak', 'sabah'],
    
    'Singapore': ['singapore', 'singapore city', 'jurong', 'woodlands', 'tampines', 'ang mo kio', 'bedok', 'sengkang', 'punggol'],
    
    'Turkey': ['turkey', 'türkiye', 'istanbul', 'ankara', 'izmir', 'bursa', 'adana', 'gaziantep', 'konya', 'antep', 'mersin', 'eskişehir', 'antalya', 'kayseri', 'samsun', 'bosphorus'],
    
    'Saudi Arabia': ['saudi', 'saudi arabia', 'riyadh', 'jeddah', 'makkah', 'medina', 'dammam', 'khobar', 'dhahran', 'tabuk', 'buraydah', 'abha', 'khobar', 'hail', 'jubail', 'yanbu'],
    
    'UAE': ['uae', 'united arab emirates', 'dubai', 'abu dhabi', 'sharjah', 'ajman', 'ras al khaimah', 'fujairah', 'umm al quwain'],
    
    'Iran': ['iran', 'tehran', 'mashhad', 'isfahan', 'karaj', 'shiraz', 'tabriz', 'qom', 'ahvaz', 'kermanshah', 'urmia', 'rasht', 'zahedan', 'hamadan', 'arak', 'yazd', 'hormuz'],
    
    'Israel': ['israel', 'jerusalem', 'tel aviv', 'haifa', 'rishon lezion', 'petah tikva', 'ashdod', 'netanya', 'beersheba', 'holon', 'bat yam', 'ramat gan', 'ashkelon', 'rehovot', 'herzliya', 'gaza'],
    
    'Russia': ['russia', 'moscow', 'st petersburg', 'novosibirsk', 'yekaterinburg', 'kazan', 'nizhny novgorod', 'chelyabinsk', 'omsk', 'samara', 'rostov-on-don', 'ufa', 'krasnoyarsk', 'voronezh', 'perm', 'volgograd', 'saratov', 'tyumen', 'tolyatti', 'izhevsk', 'barnaul', 'ulyanovsk', 'irkutsk', 'khabarovsk', 'vladivostok', 'yaroslavl', 'makhachkala', 'tomsk', 'orenburg', 'kemerovo', 'novokuznetsk', 'ryazan', 'astra',
    'astrakhan', 'naberezhnye chelny', 'penza', 'lipetsk'],
    
    'Ukraine': ['ukraine', 'kyiv', 'kiev', 'kharkiv', 'odessa', 'dnipro', 'donetsk', 'zaporizhzhia', 'lviv', 'kryvyi rih', 'mykolaiv', 'mariupol', 'lugansk', 'vinnytsia', 'kherson', 'poltava', 'chernihiv', 'cherkasy', 'sumy', 'zhytomyr', 'ivano-frankivsk', 'ternopil'],
    
    'Australia': ['australia', 'sydney', 'melbourne', 'brisbane', 'perth', 'adelaide', 'gold coast', 'newcastle', 'canberra', 'wollongong', 'logan city', 'hobart', 'geelong', 'townsville', 'cairns', 'darwin'],
    
    'New Zealand': ['new zealand', 'zealand', 'auckland', 'wellington', 'christchurch', 'hamilton', 'tauranga', 'dunedin', 'palmerston north'],
    
    # Africa
    'South Africa': ['south africa', 'johannesburg', 'cape town', 'durban', 'pretoria', 'port elizabeth', 'bioemfontein', 'pietermaritzburg', 'east london', 'rustenburg', 'mbombela', 'kimberley', 'polokwane'],
    
    'Nigeria': ['nigeria', 'lagos', 'abuja', 'kano', 'ibadan', 'port harcourt', 'benin city', 'onitsha', 'aba', 'kaduna', 'enugu', 'warri', 'jos', 'sokoto', 'ilorin', 'maiduguri'],
    
    'Egypt': ['egypt', 'cairo', 'alexandria', 'giza', 'port said', 'suez', 'luxor', 'asyut', 'ismailia', 'fayyum', 'zagazig', 'sohag', 'damietta', 'mansoura'],
    
    'Kenya': ['kenya', 'nairobi', 'mombasa', 'kisumu', 'nakuru', 'eldoret', 'thika', 'malindi', 'kitale', 'garissa', 'naivasha', 'nanyuki', 'meru'],
    
    'Ghana': ['ghana', 'accra', 'kumasi', 'tamale', 'takoradi', 'tema', 'cape coast', 'ashaiman', 'obuasi', 'sunyani', 'koforidua', 'techiman'],
    
    'Morocco': ['morocco', 'casablanca', 'rabat', 'fes', 'marrakech', 'agadir', 'tangier', 'meknes', 'oujda', 'kenitra', 'tetouan', 'safi', 'el jadida'],
    
    # Middle East
    'Qatar': ['qatar', 'doha', 'al rayyan', 'al khor', 'al wakra', 'mesaieed'],
    
    'Kuwait': ['kuwait', 'kuwait city', 'salmiya', 'hawalli', 'fahaheel', 'jabriya', 'farwaniya', 'mubarak al-kabeer'],
    
    'Oman': ['oman', 'muscat', 'salalah', 'suhar', 'nizwa', 'saham', 'ibri', 'sama'il'],
    
    'Bahrain': ['bahrain', 'manama', 'muharraq', 'rifa', 'hamad town', 'sitrah', 'budaiya'],
    
    'Jordan': ['jordan', 'amman', 'zarqa', 'irbid', 'russeifa', 'aqaba', 'madaba', 'jerash', 'karak', 'mafraq'],
    
    'Lebanon': ['lebanon', 'beirut', 'tripoli', 'sidon', 'tyre', 'nabatieh', 'jounieh', 'zahle', 'baalbek'],
    
    # Central Asia
    'Kazakhstan': ['kazakhstan', 'almaty', 'astana', 'shymkent', 'karaganda', 'aktobe', 'taraz', 'pavlodar', 'ostan', 'semey', 'atyrau', 'kostanay'],
    
    'Uzbekistan': ['uzbekistan', 'tashkent', 'samarkand', 'namangan', 'andijan', 'bukhara', 'nukus', 'qarshi', 'fergana', 'khiva', 'kokand'],
    
    'Pakistan': ['pakistan', 'karachi', 'lahore', 'faisalabad', 'rawalpindi', 'multan', 'hyderabad', 'gujranwala', 'peshawar', 'quetta', 'islamabad', 'sialkot', 'bahawalpur', 'sukkur', 'larkana', 'sheikhupura', 'mardan', 'kashmir'],
    
    'Bangladesh': ['bangladesh', 'dhaka', 'chittagong', 'khulna', 'rajshahi', 'sylhet', 'barisal', 'rangpur', 'comilla', 'mymensingh', 'gazipur', 'narayanganj'],
    
    'Sri Lanka': ['sri lanka', 'colombo', 'dehiwala', 'moratuwa', 'kandy', 'galle', 'jaffna', 'negombo', 'trincomalee', 'anuradhapura', 'kurunegala', 'ratnapura'],
    
    # Southeast Asia
    'Myanmar': ['myanmar', 'yangon', 'mandalay', 'naypyidaw', 'bago', 'mawlamyine', 'sittwe', 'pathein', 'taunggyi', 'myeik', 'pyay', 'mogok'],
    
    'Cambodia': ['cambodia', 'phnom penh', 'siem reap', 'battambang', 'sihanoukville', 'kampong cham', 'poipet', 'takhmao', 'kandal'],
    
    'Laos': ['laos', 'vientiane', 'luang prabang', 'pakse', 'thakhek', 'savannakhet', 'phonsavan', 'xam neua'],
    
    # Caribbean
    'Jamaica': ['jamaica', 'kingston', 'montego bay', 'spanish town', 'portmore', 'negri'],
    
    'Cuba': ['cuba', 'havana', 'santiago', 'camaguey', 'holguin', 'guantanamo', 'santa clara', 'bayamo'],
    
    'Dominican Republic': ['dominican republic', 'santo domingo', 'santiago', 'puerto plata', 'la romana', 'san pedro de macoris', 'higüey', 'san cristobal'],
    
    'Puerto Rico': ['puerto rico', 'san juan', 'bayamon', 'carolina', 'ponce', 'caguas', 'guaynabo', 'arecibo', 'trujillo alto'],
    
    # Pacific
    'Fiji': ['fiji', 'suva', 'nadi', 'lautoka', 'labasa', 'ba', 'sigatoka', 'levuka', 'tavua'],
    
    'Timor-Leste': ['timor', 'timor-leste', 'dili', 'venilale', 'baucau', 'maliana', 'lospalos', 'manatuto', 'same'],
    
    'Papua New Guinea': ['papua new guinea', 'port moresby', 'lae', 'mount hagen', 'madang', 'goroka', 'kavieng', 'wewak', 'kimbe'],
}

# ============================================
# EVENT CLASSIFICATION IMPROVEMENT
# ============================================
SUPPLY_CHAIN_EVENT_TYPES = {
    'war': {
        'keywords': ['war', 'conflict', 'attack', 'invasion', 'missile', 'drone strike', 'troops', 'casualties'],
        'supply_chain_impact': ['Military conflict disrupting supply routes', 'Trade restrictions', 'Sanctions']
    },
    'natural_disaster': {
        'keywords': ['earthquake', 'flood', 'hurricane', 'typhoon', 'cyclone', 'wildfire', 'drought', 'tsunami', 'storm'],
        'supply_chain_impact': ['Disruption to manufacturing', 'Logistics delays', 'Infrastructure damage']
    },
    'sanctions': {
        'keywords': ['sanctions', 'embargo', 'trade ban', 'tariff', 'restrictions'],
        'supply_chain_impact': ['Trade restrictions', 'Alternative sourcing required', 'Price volatility']
    },
    'strike': {
        'keywords': ['strike', 'walkout', 'labor dispute', 'union', 'protest', 'blockade'],
        'supply_chain_impact': ['Port/warehouse closures', 'Logistics delays', 'Production slowdown']
    },
    'shipping': {
        'keywords': ['shipping', 'canal', 'strait', 'vessel', 'tanker', 'port', 'cargo'],
        'supply_chain_impact': ['Shipping route disruption', 'Increased freight costs', 'Delivery delays']
    },
    'pandemic': {
        'keywords': ['outbreak', 'epidemic', 'pandemic', 'virus', 'disease', 'quarantine'],
        'supply_chain_impact': ['Workforce shortages', 'Factory closures', 'Border closures']
    }
}

# ============================================
# DATA QUALITY FUNCTIONS
# ============================================

def is_supply_chain_related(title: str, description: str) -> bool:
    """
    Determine if an event is supply chain related
    Returns True if event affects supply chains
    """
    text = (title + " " + (description or "")).lower()
    
    # Check for supply chain keywords
    for keyword in SUPPLY_CHAIN_KEYWORDS:
        if keyword.lower() in text:
            return True
    
    # Check for event types that affect supply chains
    for event_type, data in SUPPLY_CHAIN_EVENT_TYPES.items():
        if any(kw in text for kw in data['keywords']):
            return True
    
    return False

def enrich_location(title: str, description: str, current_country: Optional[str] = None) -> Optional[str]:
    """
    Enrich location information using keyword matching
    """
    # If already has a valid country, keep it
    if current_country and current_country not in ['Unknown', 'null', 'N/A', None]:
        return current_country
    
    text = (title + " " + (description or "")).lower()
    
    # Try to find location from keywords
    for country, keywords in LOCATION_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return country
    
    return "Unknown"

def classify_event_type(title: str, description: str) -> str:
    """
    Improved event classification focusing on supply chain impact
    """
    text = (title + " " + (description or "")).lower()
    
    # Check each event type
    for event_type, data in SUPPLY_CHAIN_EVENT_TYPES.items():
        if any(kw in text for kw in data['keywords']):
            return event_type
    
    # If not classified, check if supply chain related
    if is_supply_chain_related(title, description):
        return "supply_chain_other"
    
    return "non_supply_chain"

def calculate_supply_chain_impact(title: str, description: str, severity: int) -> Dict[str, Any]:
    """
    Calculate supply chain impact score and affected areas
    """
    text = (title + " " + (description or "")).lower()
    
    # Base impact from severity
    impact_score = severity * 10
    
    # Additional impact factors
    impact_factors = {
        'shipping': 15 if any(kw in text for kw in ['ship', 'port', 'canal', 'strait']) else 0,
        'manufacturing': 15 if any(kw in text for kw in ['factory', 'plant', 'production']) else 0,
        'raw_materials': 15 if any(kw in text for kw in ['oil', 'gas', 'wheat', 'copper']) else 0,
        'logistics': 10 if any(kw in text for kw in ['truck', 'rail', 'warehouse']) else 0,
        'geopolitical': 20 if any(kw in text for kw in ['war', 'sanctions', 'conflict']) else 0
    }
    
    total_impact = impact_score + sum(impact_factors.values())
    
    # Determine affected supply chain areas
    affected_areas = []
    if impact_factors['shipping'] > 0:
        affected_areas.append('Logistics & Transportation')
    if impact_factors['manufacturing'] > 0:
        affected_areas.append('Manufacturing')
    if impact_factors['raw_materials'] > 0:
        affected_areas.append('Raw Materials')
    if impact_factors['logistics'] > 0:
        affected_areas.append('Warehousing & Distribution')
    if impact_factors['geopolitical'] > 0:
        affected_areas.append('Trade & Geopolitical')
    
    return {
        'impact_score': min(100, total_impact),
        'affected_areas': affected_areas if affected_areas else ['General Supply Chain'],
        'severity_boosted': impact_score
    }