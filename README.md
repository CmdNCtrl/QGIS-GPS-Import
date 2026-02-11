# Import GaiaGPS KML or KMZ into QGIS

## Purpose

Are you a big fan of GaiaGPS? Do you also like to geek out on GIS data in QGIS? Do you want to be able to view and analyze your GaiaGPS data in QGIS? You've come to the right place! 
This QGIS Processing Model imports a KML/KMZ export from GaiaGPS so that you can view all your GaiaGPS recorded tracks and way points in QGIS. 

This model has the following features:

* Imports a **GaiaGPS-exported KML/KMZ** file and extacts the **Tracks** and **Waypoints** and puts them in tables called `GPS_Points` and `GPS_Lines`
* Extracts the following information from the GaiaGPS metadata and loads it to explicit fields in the tables.  Additional attributes will be added in future releases. 
  * **Tracks (lines)**
    * Name
    * Description
    * Recorded On
    * Imported At (Set to the time/date import was run in UTC)
    * Total Distance (in Meters)
    * Source (GaiaGPS)
    * Geometry
  * **Waypoints (points)**
    * Name
    * Description
    * Recorded On
    * Imported At (Set to the time/date import was run in UTC)
    * Source (GaiaGPS)
    * Geometry

* Checks to see if the **tracks** and **waypoints** already exist in the above mentioned tables based on the recorded date/time and drops any duplicates. The benefit of this is if you do periodic export of GaiGPS into QGIS, you don't necessarily need to remember if you already imported a specific **track** or **waypoint**.  The tool will check to see if they are already there and will only load the new records.  
* Extracts any photos that are associated with the extracted **Waypoints** and puts them in a `/photos` folder inside the QGIS **Project Home** (`@project_home`) folder.
* Allows you to view the photos associated with you **Waypoints** right in your QGIS Attributes Form.  The processing model sets up the Descrption_HTML field with the proper path to display your photos.  You will just need to configure the descrption_html field to be multiple lines and display as HTML.
  
---

## Requirements

### QGIS

* Built for QGIS 3.x (your project history suggests you’re on ~3.44.x).

### Operating System
 * Mac OS
 * Windows - Should work, but untested (If you test it, let me know)
 * Linux - Should work, but untested (If you test it, let me know)

### Plugins used

1. **KML Tools**
   Used by the algorithm: `kmltools:importkml`
   Purpose: imports the KML/KMZ and outputs a point layer + line layer.

2. **ETL Load** (Append Features to Layer)
   Used by the algorithm: `etl_load:appendfeaturestolayer`
   Purpose: appends new features into your existing GeoPackage layers.

---

## Installation / Set Up

1. Download the lastest released version. It contains 3 main components:
   * `Import and Process GPS KML or KMZ.model3` - The **Process Model** that you will run within QGIS
   * `ExtractPhotosFromKMZ.py` - A Python Script that exports your photos from the KMZ file. You don't need to run this alone, it gets called by the **Process Model**
   * `GaiaGPS GeoPackage.gpkg` - Lines and Points table templates inside a GeoPackage that is populated by the **Process Model**
2. Place the following files in the described locations:
   * Copy `Import and Process GPS KML or KMZ.model3` to your process model directory.  Check here to find what yours is set to: Processing -> Toolbox -> Options -> Processing -> Models 
   * Copy `ExtractPhotosFromKMZ.py` to your QGIS scripts directory Check here to find what yours is set to: Processing -> Toolbox -> Options -> Processing -> Scripts 
   * Copy `GaiaGPS GeoPackage.gpkg` to your project directory

3. This model relies on `@project_home` (your QGIS Project Home path). Set the project home to the folder that contains your QGIS project file. The script creates a `/photos` folder in this locaton so it is recommend that your put your project file in it's over folder. Set your `@project_home` here: Project -> Properties -> General

## How to Use

1. Go to GaiaGPS and export a KMZ file which contains the detail you wish to import to QGIS. (follow instructions on GaiaGPS.com for this step)
2. After following the steps above, open your project in QGIS and open the **Processing Toolbox** pane (Processing -> Toolbox
3. At the bottom of the **Processing Toolbox** frame, you will see a section called **Models**
4. Expand **Models** and you should see the model called **Import and Process GPS KML or KMZ**
5. Select **Import and Process GPS KML or KMZ**, right click and select **Execute...**
6. Select the KMZ file that you extracted from GaiaGPS in step one and click **Run**
7. All your data should be loaded to to the tables. **Waypoints** will be loaded to the table **GPS_Points** and **Tracks** will be loaded to the table **GPS_Tracks**.

### Photos Associated with you Waypoints

This tool will extract any photos that are associated with your **Waypoints** to a folder called `/photos' that is contained in the **Project Home**.  This is the location you set in step 3, in **Installation / Set Up**. 
**NOTE:** There appears to be a bug in the GaiaGPS export where, in some circumstances, not all photos are exported.  This has been reported to GaiaGPS.  If it happens to you, you can report the issue at: https://help.gaiagps.com/hc/en-us , **Contact Support**.  

#### Viewing your Photos in QGIS

Your photos will appear in field called `description_html`.  For them to appear properly, you will need to change to view your photos in QGIS, you will need to change the diplay options of the `description_html` field.  

1. Right click on on the **GPS_Points** table and select **Properties**
2. Go to **Attributes Form**
3. Select **Drag and Drop Designer** from the dropdown at the top of the screen
3. Click on `description_html`
4. Under **Widget Type**, check the **Multiline** box and the **HTML** checkbox
5. Click Ok

<img width="1071" height="797" alt="Screenshot 2026-02-07 at 10 24 40 AM" src="https://github.com/user-attachments/assets/b081b4e3-bb83-495d-9420-aaedc3383a83" />

This **Process Model** writes the path to your photos in the `description_html` field.  If you move your project folder, it will break the link.  Future releaseas might have an option to update the path if you move the project.  


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

* `end_point_description`

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

### 7) DEPRECATED: Create `match_key` for de-duplication

This step is still in the process and this field may have some value but the script has been update to use the **Recorded** date to check if the records are new or not.  

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
* Join field: `recorded`
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
## Extract KMZ Photos (Processing Script)

This project includes a custom **QGIS Processing** Python script that extracts embedded photos from a **GaiaGPS-exported `.kmz`** file (KMZ is a ZIP container) and copies any `.jpg` / `.jpeg` images into this project’s photos folder.

### What it does
- Opens the input **KMZ** (ZIP) and finds all files ending in **`.jpg`** or **`.jpeg`**
- Copies those images to the destination photos folder (by default: `@project_home/photos`)
- Optionally **flattens** subfolders (recommended), so all photos land in a single folder
- Optionally **overwrites** existing files or skips them
- Streams files directly from the zip (does not extract the whole KMZ to disk)

### Inputs / Parameters
- **Input KMZ**: Path to a GaiaGPS-exported `.kmz`
- **Photos folder**: Destination directory for extracted images  
  - Recommended: `@project_home || '/photos'`
- **Flatten subfolders** (boolean, default: `true`): Keep only filenames (ignore KMZ internal folder structure)
- **Overwrite existing files** (boolean, default: `false`): Replace files in the destination if they already exist

### Output
- A folder containing the extracted JPG images (e.g. `@project_home/photos`)
- The Processing log will report how many images were **extracted** and how many were **skipped**

### How it fits into the QGIS Model
In the Processing Model Designer, this script is typically run near the end of the workflow:

1. **Create directory** → `@project_home || '/photos'`
2. **Extract KMZ photos** → copies photos from the KMZ to that folder

This keeps the workflow portable, because it uses the QGIS project’s home directory rather than hard-coded paths.

### Cross-platform notes (macOS / Windows)
- The script uses only standard Python libraries (`zipfile`, `os`, `shutil`) and is cross-platform.
- If you use `@project_home` (or `QgsProject.instance().homePath()` in defaults), output paths are portable across operating systems.

### Future plugin plan
This script is written as a **Processing algorithm**, which makes it easy to later bundle into a QGIS plugin as part of a **Processing provider**, alongside the model and any supporting utilities.


---

## Troubleshooting Notes

* **GeoPackage locked / sqlite open errors:** close other QGIS projects or processes that might be holding the `.gpkg` open.
* **Project Home not set:** ensure your project has a valid `@project_home` (Project Properties → General → Project Home).
* **Plugins missing:** if `kmltools:*` or `etl_load:*` algorithms aren’t found, install/enable the plugins.
* **Images not rendering in forms:** confirm photos exist at `@project_home/photos/` and that the description HTML references match actual filenames.

---

