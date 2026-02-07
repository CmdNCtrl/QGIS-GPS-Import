# Import GaiaGPS KML or KMZ into QGIS

## Purpose

Are you a big fan of GaiaGPS? Do you also like to geek out on GIS data in QGIS? Do you want to be able to view and analyze your GaiaGPS data in QGIS? You've come to the right place! 
This QGIS Processing Model imports a KML/KMZ export from GaiaGPS so that you can view all your GaiaGPS recorded tracks and way points in QGIS. This model has the following features:

* Imports a **GaiaGPS-exported KML/KMZ** file and extacts the points and lines and puts them in tables called `GPS_Points` and `GPS_Lines`
* Extracts the following information from the GaiaGPS metadata and loads it to explicit fields in the tables
  * **Tracks (lines)**
    * Name
    * Description
    * Recorded On
    * Imported At
    * Total Distance
    * Source (GaiaGPS)
  * **Waypoints (points)**
    * Name
    * Description
    * Recorded On
    * Imported At
    * Source (GaiaGPS)

* Checks to see if the tracks and points already exist in the above mentioned tables based on the recorded date/time and drops any duplicates.
* Extracts any photos that are associated with the extracted **Waypoints** and puts them in a `/photos` folder inside the QGIS **Project Home** (`@project_home`) folder.
* Allows you to view the photos associated with you **Waypoints** right in your QGIS Attributes Form.  The processing model sets up the Descrption_HTML field with the proper path to display your photos.  You will just need to configure the descrption_html field to be multiple lines and display as HTML.  



---

## Requirements

### QGIS

* Built for QGIS 3.x (your project history suggests you’re on ~3.44.x).

### Plugins used

1. **KML Tools**
   Used by the algorithm: `kmltools:importkml`
   Purpose: imports the KML/KMZ and outputs a point layer + line layer.

2. **ETL Load** (Append Features to Layer)
   Used by the algorithm: `etl_load:appendfeaturestolayer`
   Purpose: appends new features into your existing GeoPackage layers.

### General

#### Path Settings:

Set the Project Home `@Project_home` variable to be the folder where your project file will be stored.  
For example, if this is the path to your project:

`/Users/UserHome/Documents/GIS/QGIS/Projects/GaiaGPS/GaiaGPS.qgz`

set your `@Project_home` to be:

`/Users/UserHome/Documents/GIS/QGIS/Projects/GaiaGPS`


This will cause the photos assocated with your GPS Points to be stored in: 

`/Users/UserHome/Documents/GIS/QGIS/Projects/GaiaGPS/photos`

---

## Installation / Set Up

1. Download the lastest released version
2. Place the following files in the described locations:
 * `Import and Process GPS KML or KMZ.model3` - Process Model -  copy to your process model directory
 * `ExtractPhotosFromKMZ.py` - Python Script - Copy to your QGIS scripts directory
 * `GaiaGPS GeoPackage.gpkg` - Lines and Points table templates inside a GeoPackage that is populated by the Process Model - Copy to your project directory

3. This model relies on `@project_home` (your QGIS Project Home path). Set the project home to the folder that contains your QGIS project file. The script creates a `/photos` folder in this locaton so it is recommend that your put your project file in it's over folder. 



---

## Inputs

### Model Parameter

* **Select KML or KMZ File** (`select_kml_or_kmz_file`)

  * Type: file
  * File filter: All files (*.*)

---

## Outputs (What Gets Updated)

### GeoPackage Targets (must already exist. A template GeoPackage containing these tables is included in the release)

* `GPS_Points`
* `GPS_Lines`

### GeoPackage Temp Tables (created/overwritten by the model)

* `GPS_Points_Temp`
* `GPS_Lines_Temp`

These temp outputs are used so the model can reliably produce “new-only” layers for appending.

---

## What the Model Does (Step-by-step)
It is not necessary for you to understand this section in order to use this tool, it is only provided if you have interest in how this works.  

### 1) Import the KML/KMZ

* **Algorithm:** `kmltools:importkml`
* Output includes:

  * `PointOutputLayer`
  * `LineOutputLayer`

### 2) Create a single “run timestamp”

* **Algorithm:** `native:calculateexpression`
* Expression: `now()`
* Stored as a model output variable used later:

  * `@Calculate_expression_Set_Runtime_OUTPUT`

This ensures points and lines in the same run share the exact same `imported_at` value.

### 3) Isolate “(End)” points

* **Algorithm:** `native:extractbyexpression`
* Expression:

  * `"name" = '(End)'`

This produces a layer of just the endpoint markers.

### 4) Join endpoint description onto lines

* **Algorithm:** `native:joinattributestable`
* Join field: `folders` (lines ↔ end points)
* Copies: `description`
* Prefix: `end_point_`

This creates/uses an endpoint-derived field named:

* `end_point_description`  ✅ (this is the intended spelling)

### 5) Refactor fields (Points)

* **Algorithm:** `native:refactorfields`
* Produces a cleaned points schema including:

  * `recorded` parsed from `description` (supports `Time Created:`, `Time Started:`, or `Recorded:` variants)
  * `imported_at` set from `@Calculate_expression_Set_Runtime_OUTPUT`
  * `description_html` which rewrites `<img src="...">` paths to point to `@project_home/photos/...`
  * `source` hard-coded to `'GaiaGPS'`

### 6) Refactor fields (Lines)

* **Algorithm:** `native:refactorfields`
* Produces a cleaned lines schema including:

  * `description` set to `"end_point_description"` (line description becomes the endpoint description)
  * `recorded` parsed from `end_point_description` (specifically the `Recorded:` segment)
  * `total_distance` parsed and converted to meters (supports `mi` and `ft`)
  * `imported_at` set from `@Calculate_expression_Set_Runtime_OUTPUT`
  * `source` hard-coded to `'GaiaGPS'`

### 7) Create `match_key` for de-duplication

* **Algorithm:** `native:fieldcalculator` (run once for points, once for lines)
* Field: `match_key`
* Formula:

  * `"source" || '|' || "folders" || '|' || "name"`

This is the key used to determine whether a record already exists in the target tables.

### 8) Write temp layers to GeoPackage (workaround)

The field calculator steps write to:

* `GPS_Points_Temp`
* `GPS_Lines_Temp`

using OGR connection strings like:

* `ogr:dbname='<project_home>/GeoPackage/GaiaGPS GeoPackage.gpkg' table="GPS_Points_Temp" (geom)`
* `ogr:dbname='<project_home>/GeoPackage/GaiaGPS GeoPackage.gpkg' table="GPS_Lines_Temp" (geom)`

**Why:** the model notes a QGIS issue where outputting the “unjoined/non-matching” results to a temporary layer can fail, but outputting to a GeoPackage succeeds (see QGIS issue referenced in-model: #39754).

### 9) Identify *new-only* records

* **Algorithm:** `native:joinattributestable` (run once for points, once for lines)
* Join field: `match_key`
* Join temp layer ↔ target layer (`GPS_Points` / `GPS_Lines`)
* Uses the model’s NON_MATCHING output to isolate records that do not already exist.

### 10) Append new records into targets

* **Algorithm:** `etl_load:appendfeaturestolayer`
* Appends:

  * new points → `GPS_Points`
  * new lines → `GPS_Lines`

---

## Target Table Requirements (Schema Expectations)

At minimum, your target layers need to support the fields the model appends, including:

* `source` (text)
* `folders` (text)
* `name` (text)
* `match_key` (text)
* `recorded` (datetime)
* `imported_at` (datetime)

Additionally:

* Points include `description_html`
* Lines include `total_distance`
* Lines workflow uses `end_point_description` during processing (result depends on how your target schema is set up)

Best practice: keep the target schema aligned with the refactor output schema so appends don’t drop fields or fail.

---

## Troubleshooting Notes

* **GeoPackage locked / sqlite open errors:** close other QGIS projects or processes that might be holding the `.gpkg` open.
* **Project Home not set:** ensure your project has a valid `@project_home` (Project Properties → General → Project Home).
* **Plugins missing:** if `kmltools:*` or `etl_load:*` algorithms aren’t found, install/enable the plugins.
* **Images not rendering in forms:** confirm photos exist at `@project_home/photos/` and that the description HTML references match actual filenames.

---

