"""Seed data for Phase 2 features (hospitals, transport, traffic, explore India)."""

CITIES = [
    {"name": "Nagpur", "state": "Maharashtra", "lat": 21.1458, "lng": 79.0882},
    {"name": "Mumbai", "state": "Maharashtra", "lat": 19.0760, "lng": 72.8777},
    {"name": "Pune", "state": "Maharashtra", "lat": 18.5204, "lng": 73.8567},
    {"name": "Delhi", "state": "Delhi", "lat": 28.6139, "lng": 77.2090},
    {"name": "Bengaluru", "state": "Karnataka", "lat": 12.9716, "lng": 77.5946},
    {"name": "Hyderabad", "state": "Telangana", "lat": 17.3850, "lng": 78.4867},
    {"name": "Ahmedabad", "state": "Gujarat", "lat": 23.0225, "lng": 72.5714},
    {"name": "Jaipur", "state": "Rajasthan", "lat": 26.9124, "lng": 75.7873},
    {"name": "Lucknow", "state": "Uttar Pradesh", "lat": 26.8467, "lng": 80.9462},
    {"name": "Kolkata", "state": "West Bengal", "lat": 22.5726, "lng": 88.3639},
    {"name": "Chennai", "state": "Tamil Nadu", "lat": 13.0827, "lng": 80.2707},
    {"name": "Bhopal", "state": "Madhya Pradesh", "lat": 23.2599, "lng": 77.4126},
]

HOSPITALS = [
    {"id": "h1", "name": "AIIMS Nagpur", "city": "Nagpur", "address": "Plot No. 2, Sector 20, MIHAN, Nagpur", "phone": "+91 712 220 5000", "emergency": True, "lat": 21.0996, "lng": 79.0466},
    {"id": "h2", "name": "Government Medical College", "city": "Nagpur", "address": "Hanuman Nagar, Nagpur", "phone": "+91 712 270 1145", "emergency": True, "lat": 21.1310, "lng": 79.0640},
    {"id": "h3", "name": "Wockhardt Hospital", "city": "Nagpur", "address": "North Ambazari Road, Nagpur", "phone": "+91 712 663 3300", "emergency": True, "lat": 21.1420, "lng": 79.0625},
    {"id": "h4", "name": "Tata Memorial Hospital", "city": "Mumbai", "address": "Dr E Borges Road, Parel, Mumbai", "phone": "+91 22 2417 7000", "emergency": True, "lat": 19.0009, "lng": 72.8425},
    {"id": "h5", "name": "AIIMS Delhi", "city": "Delhi", "address": "Ansari Nagar, New Delhi", "phone": "+91 11 2658 8500", "emergency": True, "lat": 28.5672, "lng": 77.2100},
    {"id": "h6", "name": "Manipal Hospital", "city": "Bengaluru", "address": "HAL Airport Road, Bengaluru", "phone": "+91 80 2502 4444", "emergency": True, "lat": 12.9584, "lng": 77.6485},
    {"id": "h7", "name": "Apollo Hospital", "city": "Hyderabad", "address": "Jubilee Hills, Hyderabad", "phone": "+91 40 2360 7777", "emergency": True, "lat": 17.4126, "lng": 78.4071},
    {"id": "h8", "name": "SMS Hospital", "city": "Jaipur", "address": "JLN Marg, Jaipur", "phone": "+91 141 256 0291", "emergency": True, "lat": 26.9021, "lng": 75.8145},
]

TRANSPORT_ROUTES = [
    {"id": "t1", "from": "Sitabuldi", "to": "Airport", "city": "Nagpur", "mode": "Bus", "duration": "35 min", "stops": ["Sitabuldi", "Rahate Colony", "Wardha Road", "MIHAN", "Airport"]},
    {"id": "t2", "from": "Nagpur Railway Station", "to": "Sitabuldi", "city": "Nagpur", "mode": "Metro", "duration": "12 min", "stops": ["Railway Station", "Cotton Market", "Sitabuldi"]},
    {"id": "t3", "from": "Sitabuldi", "to": "Kamptee Road", "city": "Nagpur", "mode": "Bus", "duration": "28 min", "stops": ["Sitabuldi", "Panchsheel", "Kadbi Chowk", "Kamptee Road"]},
    {"id": "t4", "from": "Bandra", "to": "Andheri", "city": "Mumbai", "mode": "Local Train", "duration": "18 min", "stops": ["Bandra", "Khar", "Santacruz", "Vile Parle", "Andheri"]},
]

TRAFFIC_INCIDENTS = [
    {"id": "tr1", "city": "Nagpur", "type": "Congestion", "location": "Wardha Road near Airport", "severity": "HIGH", "description": "Heavy traffic due to office hours.", "lat": 21.0930, "lng": 79.0500},
    {"id": "tr2", "city": "Nagpur", "type": "Road Work", "location": "Kamptee Road", "severity": "MEDIUM", "description": "Lane closed for pipeline repair.", "lat": 21.1855, "lng": 79.1050},
    {"id": "tr3", "city": "Nagpur", "type": "Accident", "location": "Ring Road Junction", "severity": "CRITICAL", "description": "Two vehicles involved. Expect delays.", "lat": 21.1220, "lng": 79.0910},
    {"id": "tr4", "city": "Mumbai", "type": "Congestion", "location": "Western Express Highway", "severity": "HIGH", "description": "Peak hour congestion.", "lat": 19.1075, "lng": 72.8377},
]

SOS_SERVICES = [
    {"type": "Police", "phone": "100", "icon": "shield"},
    {"type": "Ambulance", "phone": "102", "icon": "ambulance"},
    {"type": "Fire", "phone": "101", "icon": "flame"},
    {"type": "Emergency", "phone": "112", "icon": "siren"},
    {"type": "Women Helpline", "phone": "1091", "icon": "user"},
    {"type": "Child Helpline", "phone": "1098", "icon": "baby"},
]

EXPLORE_PLACES = [
    {"id": "e1", "name": "Taj Mahal", "state": "Uttar Pradesh", "city": "Agra", "category": "Heritage", "description": "17th-century ivory-white marble mausoleum, an icon of Indian heritage.", "image": "https://images.pexels.com/photos/11948442/pexels-photo-11948442.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940", "lat": 27.1751, "lng": 78.0421},
    {"id": "e2", "name": "Gateway of India", "state": "Maharashtra", "city": "Mumbai", "category": "Heritage", "description": "Arch monument built in the 20th century on the waterfront in Mumbai.", "image": "https://images.unsplash.com/photo-1595658658481-d53d3f999875?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2NDF8MHwxfHNlYXJjaHwyfHxHYXRld2F5JTIwb2YlMjBJbmRpYSUyME11bWJhaXxlbnwwfHx8fDE3ODc4MjcxNjB8MA&ixlib=rb-4.1.0&q=85", "lat": 18.9220, "lng": 72.8347},
    {"id": "e3", "name": "India Gate", "state": "Delhi", "city": "Delhi", "category": "Heritage", "description": "War memorial located astride the Rajpath in New Delhi.", "image": "https://images.unsplash.com/photo-1587474260584-136574528ed5?auto=format&fit=crop&w=800", "lat": 28.6129, "lng": 77.2295},
    {"id": "e4", "name": "Charminar", "state": "Telangana", "city": "Hyderabad", "category": "Heritage", "description": "Monument and mosque located in Hyderabad, built in 1591.", "image": "https://images.unsplash.com/photo-1626196340104-fdf745f10054?auto=format&fit=crop&w=800", "lat": 17.3616, "lng": 78.4747},
    {"id": "e5", "name": "Hawa Mahal", "state": "Rajasthan", "city": "Jaipur", "category": "Forts", "description": "Palace of Winds, a five-story palace in Jaipur.", "image": "https://images.unsplash.com/photo-1477587458883-47145ed94245?auto=format&fit=crop&w=800", "lat": 26.9239, "lng": 75.8267},
    {"id": "e6", "name": "Ajanta Caves", "state": "Maharashtra", "city": "Aurangabad", "category": "Heritage", "description": "Buddhist rock-cut cave monuments dating from the 2nd century BCE.", "image": "https://images.unsplash.com/photo-1590077428593-a55bb07c4665?auto=format&fit=crop&w=800", "lat": 20.5522, "lng": 75.7033},
    {"id": "e7", "name": "Ellora Caves", "state": "Maharashtra", "city": "Aurangabad", "category": "Heritage", "description": "UNESCO World Heritage Site with 34 caves.", "image": "https://images.unsplash.com/photo-1518709414768-a88981a4515d?auto=format&fit=crop&w=800", "lat": 20.0269, "lng": 75.1793},
    {"id": "e8", "name": "Sanchi Stupa", "state": "Madhya Pradesh", "city": "Sanchi", "category": "Temples", "description": "Buddhist complex famous for its Great Stupa.", "image": "https://images.unsplash.com/photo-1618485052077-e35c2c37c9f0?auto=format&fit=crop&w=800", "lat": 23.4795, "lng": 77.7395},
    {"id": "e9", "name": "Marine Drive", "state": "Maharashtra", "city": "Mumbai", "category": "Cities", "description": "3.6-km-long boulevard on the coast of Mumbai.", "image": "https://images.unsplash.com/photo-1580060839134-75a5edca2e99?auto=format&fit=crop&w=800", "lat": 18.9435, "lng": 72.8235},
]

LANGUAGES = [
    {"code": "en", "label": "English"},
    {"code": "hi", "label": "हिन्दी"},
    {"code": "mr", "label": "मराठी"},
    {"code": "bn", "label": "বাংলা"},
    {"code": "te", "label": "తెలుగు"},
    {"code": "ta", "label": "தமிழ்"},
    {"code": "gu", "label": "ગુજરાતી"},
    {"code": "kn", "label": "ಕನ್ನಡ"},
    {"code": "ml", "label": "മലയാളം"},
    {"code": "pa", "label": "ਪੰਜਾਬੀ"},
]
