# QGIS-GPS-Import

# GaiaGPS Import & Normalization Model

## Overview
This QGIS Processing Model imports and normalizes data exported from **Gaia GPS** (KML / KMZ / GPX), producing clean, consistently structured line and point layers suitable for long-term storage in a GeoPackage and further analysis.

The model is designed to be:
- **Project-portable** (uses project-relative paths where possible)
- **Deterministic** (single run timestamp shared across outputs)
- **Idempotent** (safe to re-run without creating duplicate records)
- **Version-controlled** (stored as a standalone `.model3` file)

---

## Set Up
1)  Set Project home `@project_home` to be the folder that contains your project file
2) Install the following two plug ins:

        Append Features to Layers

        KML Tools

This model is stored as a standalone Processing Model:


It is intended to be versioned in Git alongside the QGIS project.

---

## Inputs

| Parameter | Type | Description |
|---------|------|-------------|
| Gaia GPS Input | Vector Layer / File | Gaia GPS export (KML, KMZ, or GPX) |
| Target GeoPackage | GeoPackage | Destination GeoPackage for normalized outputs |
| Import Timestamp | DateTime | Timestamp representing when the import was performed (single value applied to all records) |

> **Note:** The Import Timestamp should be provided once per run to ensure all created records share the same exact value.

---

## Outputs

| Layer | Geometry | Description |
|------|---------|-------------|
| Tracks | LineString | Normalized track geometry |
| Track Points | Point | Normalized track points |
| (Optional) Unmatched Records | Point / Line | Records that did not match an existing track or key |

All outputs are written to the target GeoPackage using consistent schemas and field naming.

---

## Key Fields

### Common Fields
| Field | Type | Description |
|-----|------|-------------|
| import_datetime | DateTime | Timestamp of import execution |
| source | Text | Source of the data (e.g., `GaiaGPS`) |

### Track Fields
| Field | Type | Description |
|------|------|-------------|
| track_id | Integer | Unique identifier for the track |
| track_name | Text | Track name from source data |

### Point Fields
| Field | Type | Description |
|------|------|-------------|
| point_id | Integer | Unique identifier for the point |
| track_id | Integer | Foreign key to parent track |
| end_point_description | Text | Description derived from source metadata |

---

## Assumptions & Requirements
- Input layers are valid and have geometries
- CRS is either WGS84 or convertible without loss
- Target GeoPackage tables already exist **or** are created by this model
- Primary keys are integer-based and auto-incremented
- Joins are performed using stable identifiers (not user-editable text fields)

---

## Portability Notes
- File paths should be **project-relative** where possible
- Absolute paths are avoided to ensure cross-machine compatibility
- The model is designed to run consistently on macOS, Windows, and Linux

---

## Versioning
This model is maintained under Git version control.

Recommended versioning scheme:
- `v1.0.0` – Initial stable release
- `v1.x.x` – Backward-compatible improvements
- `v2.0.0` – Schema or logic breaking changes

---

## Usage
1. Open the QGIS project
2. Ensure the model folder is registered in **Processing → Options → Models**
3. Run the model from the Processing Toolbox
4. Review logs for any unmatched or skipped records
5. Commit changes to the repository after successful validation

---

## Notes
- This model is intentionally project-scoped and opinionated
- Schema changes should be reflected in both the model and documentation
- Any changes that affect outputs should increment the model version

---

