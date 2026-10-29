"""Region definitions shared by the build and SST fetch. Boxes by latitude/longitude per state.
SST points are offshore ocean cells near each region's incident cluster."""
REGIONS = [
 # name, coast description, state, sst lat, sst lon
 ("NSW North Coast","Byron Bay to Coffs Harbour","NSW",-29.5,153.6),
 ("Mid North Coast & Hunter","Port Macquarie to Newcastle","NSW",-32.0,152.8),
 ("Sydney & Central Coast","Gosford to Cronulla","NSW",-33.9,151.5),
 ("NSW South Coast","Wollongong to Eden","NSW",-35.5,150.6),
 ("Gold Coast","Coolangatta to South Stradbroke","QLD",-28.0,153.75),
 ("Sunshine Coast & Moreton Bay","Noosa to Brisbane, K'gari","QLD",-26.6,153.4),
 ("Central QLD & Whitsundays","Bundaberg to Townsville","QLD",-20.5,149.5),
 ("Far North Queensland","Cairns and the northern reef","QLD",-16.5,146.0),
 ("Perth & Rottnest","Perth metro coast and islands","WA",-32.0,115.3),
 ("WA South West","Mandurah to Augusta","WA",-33.5,114.7),
 ("WA South Coast","Albany to Esperance","WA",-35.2,118.5),
 ("WA Mid West & North","Geraldton to Broome","WA",-28.8,114.3),
 ("SA Gulfs & Yorke Peninsula","Adelaide, Yorke Peninsula, Fleurieu","SA",-35.6,137.2),
 ("SA Eyre Peninsula & Bight","Port Lincoln to the Bight","SA",-33.3,134.0),
 ("Victoria","Whole coast","VIC",-39.0,144.0),
 ("Tasmania","Whole coast","TAS",-42.5,148.4),
 ("Northern Territory","Whole coast","NT",-12.2,130.6),
]

def region_of(state, lat, lon):
    s = state.strip().upper()
    if s == "QLD":
        if lat < -27.9: return "Gold Coast"
        if lat < -25.5: return "Sunshine Coast & Moreton Bay"
        if lat < -19: return "Central QLD & Whitsundays"
        return "Far North Queensland"
    if s == "NSW":
        if lat > -31: return "NSW North Coast"
        if lat > -33.3: return "Mid North Coast & Hunter"
        if lat > -34.2: return "Sydney & Central Coast"
        return "NSW South Coast"
    if s == "WA":
        if lat > -31.3: return "WA Mid West & North"
        if lon >= 116.5: return "WA South Coast"
        if lat > -32.4: return "Perth & Rottnest"
        return "WA South West"
    if s == "SA":
        return "SA Eyre Peninsula & Bight" if lon < 137 else "SA Gulfs & Yorke Peninsula"
    return {"VIC": "Victoria", "TAS": "Tasmania", "NT": "Northern Territory"}.get(s)
