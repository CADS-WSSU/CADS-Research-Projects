# Data Description
The following tables contain detailed descriptions of each of the variables in the datasets.

# Density Variables
<table>
    <tr>
        <td><b>Variable</b></td>
        <td><b>Variable Column Header</b></td>
        <td><b>Definition</b></td>
    </tr>
    <tr>
        <td>Density of Grocery Stores</td>
        <td>GroceryStores_PerSqMi</td>
        <td>Count of the number of grocery stores per sq mi</td>
    </tr>
    <tr>
        <td>Density of Pharmacies</td>
        <td>Pharmacies_PerSqMi</td>
        <td>Count of the number of pharmacies per sq mi</td>
    </tr>
    <tr>
        <td>Density of Gas Stations</td>
        <td>Gas_Stations_PerSqMi</td>
        <td>Count of the number of gas stations per sq mi</td>
    </tr>
    <tr>
        <td>Density of Nursing Homes</td>
        <td>Nursing_Homes_PerSqMi</td>
        <td>Count of the number of nursing homes per sq mi</td>
    </tr>
    <tr>
        <td>Density of Parks/Rec Facilities</td>
        <td>ParksRec_PerSqMi</td>
        <td>Count of the number of parks or recreation facilities per sq mi</td>
    </tr>
    <tr>
        <td>Density of Transit Stops</td>
        <td>TransitStops_PerSqMi</td>
        <td>Count of the number of transit stops per sq mi</td>
    </tr>
    <tr>
        <td>Density of Redlined Areas</td>
        <td>RedlinedAreas_PerSqMi</td>
        <td>Count of the number of redlined areas per sq mi</td>
    </tr>
    <tr>
        <td>Density of Fire Stations</td>
        <td>Fire_Stations_PerSqMi</td>
        <td>Count of the number of fire stations per sq mi</td>
    </tr>
    <tr>
        <td>Density of Hospitals</td>
        <td>Hospitals_PerSqMi</td>
        <td>Count of the number of hospitals per sq mi</td>
    </tr>
    <tr>
        <td>Density of Public Schools</td>
        <td>PubSchools_PerSqMi</td>
        <td>Count of the number of public schools per sq mi</td>
    </tr>
    <tr>
        <td>Density of Medical Facilities</td>
        <td>MedFacilities_PerSqMi</td>
        <td>Count of the number of medical facilities per sq mi</td>
    </tr>
    <tr>
        <td>Density of Brownfields</td>
        <td>Brownfields_PerSqMi</td>
        <td>Count of the number of brownfields per sq mi</td>
    </tr>
    <tr>
        <td>Density of Hazardous Waste Sites</td>
        <td>HazWasteFacilit_PerSqMi</td>
        <td>Count of the number of hazardous waste sites per sq mi</td>
    </tr>
    <tr>
        <td>Density of NPDES</td>
        <td>NPDES_PerSqMi</td>
        <td>Count of the number of NPDESs per sq mi</td>
    </tr>
    <tr>
        <td>Density of Regional Underground Storage (RUS)</td>
        <td>RegUndergStorage_PerSqMi</td>
        <td>Count of the number of RUS sites per sq mi</td>
    </tr>
    <tr>
        <td>Density of Public Libraries</td>
        <td>PubLibraries_PerSqMi</td>
        <td>Count of the number of public libraries per sq mi</td>
    </tr>
    <tr>
        <td>Density of Colleges</td>
        <td>Colleges_PerSqMi</td>
        <td>Count of the number of colleges per sq mi</td>
    </tr>
    <tr>
        <td>Density of Jobs</td>
        <td>Jobs_PerSqMi</td>
        <td>Count of the number of Jobs per sq mi</td>
    </tr>
</table>

# Proximity Variables

<table>
    <tr>
        <td><b>Variable</b></td>
        <td><b>Variable Column Header</b></td>
        <td><b>Definition</b></td>
    </tr>
    <tr>
        <td>Proximity to Nearest Grocery Store</td>
        <td>NEAR_GROC</td>
        <td>Distance from a census tract’s centroid to the closest grocery store</td>
    </tr>
    <tr>
        <td>Proximity to Nearest Park/Rec Facility</td>
        <td>NEAR_REC</td>
        <td>Distance from a census tract’s centroid to the closest park/rec facility</td>
    </tr>
    <tr>
        <td>Proximity to Nearest Hospital</td>
        <td>NEAR_HOSPITALS</td>
        <td>Distance from a census tract’s centroid to the closest hospital</td>
    </tr>
    <tr>
        <td>Proximity to Nearest Medical Facility</td>
        <td>NEAR_MED</td>
        <td>Distance from a census tract’s centroid to the closest medical facility</td>
    </tr>
    <tr>
        <td>Proximity to Nearest Public Library</td>
        <td>NEAR_LIBRARY</td>
        <td>Distance from a census tract’s centroid to the closest library</td>
    </tr>
    <tr>
        <td>Proximity to Nearest Interstate</td>
        <td>NEAR_INTST</td>
        <td>Distance from a census tract’s centroid to the closest interstate</td>
    </tr>
    <tr>
        <td>Proximity to Nearest Brownfield</td>
        <td>NEAR_BRWN</td>
        <td>Distance from a census tract’s centroid to the closest brownfield</td>
    </tr>
    <tr>
        <td>Proximity to Nearest Hazardous Waste Site</td>
        <td>NEAR_HAZ</td>
        <td>Distance from a census tract’s centroid to the closest hazardous waste site</td>
    </tr>
    <tr>
        <td>Proximity to Nearest Redlined Area</td>
        <td>NEAR_RED</td>
        <td>Distance from a census tract’s centroid to the closest redlined area</td>
    </tr>
    <tr>
        <td>Proximity to Work</td>
        <td>Pct_Commute_LessThan15Mins</td>
        <td>Percent of workers with commutes less than 15 minutes</td>
    </tr>
</table>

# Diversity Variables

<table>
    <tr>
        <td><b>Variable</b></td>
        <td><b>Variable Column Header</b></td>
        <td><b>Definition</b></td>
    </tr>
    <tr>
        <td>Percent Impervious Surface</td>
        <td>Percent_Impervious</td>
        <td>Percent of land that is covered by impervious surfaces</td>
    </tr>
    <tr>
        <td>Racial Segregation</td>
        <td>IsoIndex_BW_2020</td>
        <td>Measured as the Isolation Index between black and white residents</td>
    </tr>
    <tr>
        <td>Housing Stock Diversity</td>
        <td>SimpsonIndex_DivHouseStock</td>
        <td>Measured as a Simpson’s Index of diversity across the Census defined housing structure types</td>
    </tr>
</table>

# Connectivity Variables

<table>
    <tr>
        <td><b>Variable</b></td>
        <td><b>Variable Column Header</b></td>
        <td><b>Definition</b></td>
    </tr>
    <tr>
        <td>Street Connectivity</td>
        <td>STREETCON</td>
        <td>Gamma index measuring street connections</td>
    </tr>
    <tr>
        <td>Internet Fiber</td>
        <td>Pct_Pop_hasAccessFiber</td>
        <td>Percent of households with access to fiber</td>
    </tr>
    <tr>
        <td>Social Capital</td>
        <td>Overall_SelfRespRate</td>
        <td>Social capital, proxied with census return rates</td>
    </tr>
    <tr>
        <td>Internet Providers</td>
        <td>Percent_Pop_NoProvider</td>
        <td>Percent of households without access to an internet provider</td>
    </tr>
    <tr>
        <td>Transit Route</td>
        <td>Transit_Route_Indicator</td>
        <td>Indicator for whether a tract contains a public transit route</td>
    </tr>
    <tr>
        <td>Interstate</td>
        <td>Interstate_Present</td>
        <td>Indicator for whether a tract contains an interstate access point</td>
    </tr>
</table>
