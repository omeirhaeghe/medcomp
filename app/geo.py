"""City/state → metro area + US Census region lookup."""

STATE_TO_REGION = {
    # Northeast
    "CT": "Northeast", "ME": "Northeast", "MA": "Northeast", "NH": "Northeast",
    "RI": "Northeast", "VT": "Northeast", "NJ": "Northeast", "NY": "Northeast",
    "PA": "Northeast",
    # Midwest
    "IL": "Midwest", "IN": "Midwest", "MI": "Midwest", "OH": "Midwest",
    "WI": "Midwest", "IA": "Midwest", "KS": "Midwest", "MN": "Midwest",
    "MO": "Midwest", "NE": "Midwest", "ND": "Midwest", "SD": "Midwest",
    # South
    "DE": "South", "FL": "South", "GA": "South", "MD": "South", "NC": "South",
    "SC": "South", "VA": "South", "DC": "South", "WV": "South", "AL": "South",
    "KY": "South", "MS": "South", "TN": "South", "AR": "South", "LA": "South",
    "OK": "South", "TX": "South",
    # West
    "AZ": "West", "CO": "West", "ID": "West", "MT": "West", "NV": "West",
    "NM": "West", "UT": "West", "WY": "West", "AK": "West", "CA": "West",
    "HI": "West", "OR": "West", "WA": "West",
}

# (city_lower, state) -> metro
CITY_STATE_TO_METRO = {
    # NYC metro
    ("new york", "NY"): "New York City",
    ("brooklyn", "NY"): "New York City",
    ("bronx", "NY"): "New York City",
    ("flushing", "NY"): "New York City",
    ("long island", "NY"): "New York City",
    ("bay shore", "NY"): "New York City",
    ("glen oaks", "NY"): "New York City",
    ("new hyde park", "NY"): "New York City",
    ("valhalla", "NY"): "New York City",
    ("new brunswick", "NJ"): "New York City",
    ("newark", "NJ"): "New York City",
    # Boston metro
    ("boston", "MA"): "Boston",
    ("cambridge", "MA"): "Boston",
    # Philadelphia metro
    ("philadelphia", "PA"): "Philadelphia",
    ("philadelphai", "PA"): "Philadelphia",  # PDF typo
    # Pittsburgh metro
    ("pittsburgh", "PA"): "Pittsburgh",
    # Cleveland metro
    ("cleveland", "OH"): "Cleveland",
    ("cleveland hts.", "OH"): "Cleveland",
    ("cleveland heights", "OH"): "Cleveland",
    # Chicago metro
    ("chicago", "IL"): "Chicago",
    ("park ridge", "IL"): "Chicago",
    ("north chicago", "IL"): "Chicago",
    ("maywood", "IL"): "Chicago",
    ("evanston", "IL"): "Chicago",
    # Columbus metro
    ("columbus", "OH"): "Columbus",
    ("gahanna", "OH"): "Columbus",
    # Cincinnati metro
    ("cincinnati", "OH"): "Cincinnati",
    ("cincinatti", "OH"): "Cincinnati",  # PDF typo
    # Detroit metro
    ("detroit", "MI"): "Detroit",
    ("royal oak", "MI"): "Detroit",
    # Ann Arbor (its own MSA)
    ("ann arbor", "MI"): "Ann Arbor",
    # LA metro
    ("los angeles", "CA"): "Los Angeles",
    ("torrance", "CA"): "Los Angeles",
    ("torrace", "CA"): "Los Angeles",  # PDF typo
    ("downey", "CA"): "Los Angeles",
    ("orange", "CA"): "Los Angeles",
    ("murrieta", "CA"): "Los Angeles",
    # Bay Area
    ("san francisco", "CA"): "San Francisco Bay Area",
    ("stanford", "CA"): "San Francisco Bay Area",
    ("san jose", "CA"): "San Francisco Bay Area",
    ("redwood city", "CA"): "San Francisco Bay Area",
    ("oakland", "CA"): "San Francisco Bay Area",
    # San Diego
    ("san diego", "CA"): "San Diego",
    ("la jolla", "CA"): "San Diego",
    # Sacramento
    ("sacramento", "CA"): "Sacramento",
    # Fresno
    ("fresno", "CA"): "Fresno",
    # Seattle
    ("seattle", "WA"): "Seattle",
    ("tacoma", "WA"): "Seattle",
    # Portland
    ("portland", "OR"): "Portland",
    # Denver metro
    ("denver", "CO"): "Denver",
    ("aurora", "CO"): "Denver",
    # DC metro
    ("washington", "DC"): "Washington DC",
    ("bethesda", "MD"): "Washington DC",
    # Baltimore
    ("baltimore", "MD"): "Baltimore",
    # Atlanta
    ("atlanta", "GA"): "Atlanta",
    # Miami
    ("miami", "FL"): "Miami",
    ("gainesville", "FL"): "Gainesville",
    ("jacksonville", "FL"): "Jacksonville",
    ("orlando", "FL"): "Orlando",
    ("tampa", "FL"): "Tampa",
    # Houston
    ("houston", "TX"): "Houston",
    # Dallas
    ("dallas", "TX"): "Dallas-Fort Worth",
    # Austin
    ("austin", "TX"): "Austin",
    # San Antonio
    ("san antonio", "TX"): "San Antonio",
    # Nashville
    ("nashville", "TN"): "Nashville",
    # Phoenix metro
    ("mesa", "AZ"): "Phoenix",
    ("chandler", "AZ"): "Phoenix",
    ("gilbert", "AZ"): "Phoenix",
    ("phoenix", "AZ"): "Phoenix",
    # Las Vegas
    ("las vegas", "NV"): "Las Vegas",
    # Salt Lake City
    ("salt lake city", "UT"): "Salt Lake City",
    # St. Louis
    ("st louis", "MO"): "St. Louis",
    ("st. louis", "MO"): "St. Louis",
    # Providence
    ("providence", "RI"): "Providence",
    # New Haven
    ("new haven", "CT"): "New Haven",
    # Hartford / Farmington CT
    ("farmington", "CT"): "Hartford",
    # Burlington VT
    ("burlington", "VT"): "Burlington VT",
    # Hershey (Harrisburg metro)
    ("hershey", "PA"): "Harrisburg",
    # Other singletons
    ("durham", "NC"): "Raleigh-Durham",
    ("chapel hill", "NC"): "Raleigh-Durham",
    ("charleston", "SC"): "Charleston SC",
    ("winston-salem", "NC"): "Winston-Salem",
    ("madison", "WI"): "Madison",
    ("milwaukee", "WI"): "Milwaukee",
    ("waukesha", "WI"): "Milwaukee",
    ("indianapolis", "IN"): "Indianapolis",
    ("rochester", "MN"): "Rochester MN",
    ("rochester", "NY"): "Rochester NY",
    ("buffalo", "NY"): "Buffalo",
    ("syracuse", "NY"): "Syracuse",
    ("worcester", "MA"): "Worcester",
    ("portland", "ME"): "Portland ME",
    ("lebanon", "NH"): "Lebanon NH",
    ("lawrence", "MA"): "Boston",
    ("akron", "OH"): "Akron",
    ("canton", "OH"): "Akron",
    ("toledo", "OH"): "Toledo",
    ("dayton", "OH"): "Dayton",
    ("chardon", "OH"): "Cleveland",
    ("ann arbor", "MI"): "Ann Arbor",
    ("grand rapids", "MI"): "Grand Rapids",
    ("kansas city", "KS"): "Kansas City",
    ("kansas city", "MO"): "Kansas City",
    ("iowa city", "IA"): "Iowa City",
    ("omaha", "NE"): "Omaha",
    ("louisville", "KY"): "Louisville",
    ("lexington", "KY"): "Lexington",
    ("richmond", "VA"): "Richmond",
    ("charlottesville", "VA"): "Charlottesville",
    ("danville", "PA"): "Danville PA",
    ("waco", "TX"): "Waco",
    ("galveston", "TX"): "Houston",
    ("huntington", "WV"): "Huntington",
    ("lubbock", "TX"): "Lubbock",
    ("brigham", "UT"): "Salt Lake City",
    # Added for Columbia 2023
    ("tulsa", "OK"): "Tulsa",
    ("san mateo", "CA"): "San Francisco Bay Area",
    ("cooperstown", "NY"): "Cooperstown NY",
    ("marietta", "GA"): "Atlanta",
    ("stamford", "CT"): "Stamford",
    ("hollywood", "FL"): "Miami",
    ("burlington", "MA"): "Boston",
    # Added for CWRU 2023
    ("thousand oaks", "CA"): "Los Angeles",
    ("inglewood", "CA"): "Los Angeles",
    ("colton", "CA"): "Inland Empire",
    ("albuquerque", "NM"): "Albuquerque",
    ("berwyn", "IL"): "Chicago",
    ("midlothian", "VA"): "Richmond",
    ("brockton", "MA"): "Boston",
    ("tucson", "AZ"): "Tucson",
    ("joint base lewis-mcchord", "WA"): "Seattle",
    ("allentown", "PA"): "Allentown",
    ("new orleans", "LA"): "New Orleans",
    ("memphis", "TN"): "Memphis",
    ("minneapolis", "MN"): "Twin Cities",
    ("boise", "ID"): "Boise",
    ("odessa", "TX"): "Odessa",
}


def metro_for(city: str, state: str) -> str:
    """Return metro for a city/state, falling back to the city name itself."""
    if not city or not state:
        return "Unknown"
    key = (city.strip().lower(), state.strip().upper())
    return CITY_STATE_TO_METRO.get(key, city.strip())


def region_for(state: str) -> str:
    if not state:
        return "Unknown"
    return STATE_TO_REGION.get(state.strip().upper(), "Unknown")
