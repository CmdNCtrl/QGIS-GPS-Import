Below is a copy/paste **README.md** for your QGIS Processing Model (read directly from: `Import and Process GPS KML or KMZ.model3`).

---

# Import and Process GPS KML or KMZ (QGIS Model)

## Purpose

This QGIS Processing Model imports a **GaiaGPS-exported KML/KMZ**, normalizes the resulting **points** and **lines** into a consistent schema, generates a **de-duplication key (`match_key`)**, and then **appends only new records** into an existing GeoPackage:

* `GPS_Points` (target)
* `GPS_Lines` (target)

It also creates intermediate GeoPackage tables (`*_Temp`) as part of a workaround for a known QGIS Modeler output issue.

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

## Expected Project Layout

This model relies on `@project_home` (your QGIS Project Home path).

It expects the GeoPackage to be located at:

* `@project_home/GeoPackage/GaiaGPS GeoPackage.gpkg`

It also assumes photos referenced by GaiaGPS are stored at:

* `@project_home/photos/`

The model builds HTML image paths like:

* `file:///.../<project_home>/photos/<image_name>`

(Used in the `description_html` field for points.)

---

## Inputs

### Model Parameter

* **Select KML or KMZ File** (`select_kml_or_kmz_file`)

  * Type: file
  * File filter: All files (*.*)

---

## Outputs (What Gets Updated)

### GeoPackage Targets (must already exist)

* `GPS_Points`
* `GPS_Lines`

### GeoPackage Temp Tables (created/overwritten by the model)

* `GPS_Points_Temp`
* `GPS_Lines_Temp`

These temp outputs are used so the model can reliably produce “new-only” layers for appending.

---

## What the Model Does (Step-by-step)

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

## Version Control Suggestions

To track this model in Git:

* Commit the `.model3` file itself (this is the authoritative model definition).
* Keep this README in the same folder as the model.
* Optionally add a `/samples/` folder with a small example `.kmz` (if you’re okay storing one in the repo).

---

If you want, I can also generate a companion **CHANGELOG.md** format based on the dated notes embedded in the model components (1/21/25, 1/25/26, 1/27/26, etc.).
