from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterFile,
    QgsProcessingParameterFolderDestination,
    QgsProcessingParameterBoolean,
    QgsProcessingException,
)

import os
import zipfile
import shutil


class ExtractKmzPhotos(QgsProcessingAlgorithm):
    INPUT_KMZ = "INPUT_KMZ"
    OUTPUT_FOLDER = "OUTPUT_FOLDER"
    FLATTEN = "FLATTEN"
    OVERWRITE = "OVERWRITE"

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return ExtractKmzPhotos()

    def name(self):
        return "extract_kmz_photos"

    def displayName(self):
        return self.tr("Extract KMZ photos")

    def group(self):
        return self.tr("GaiaGPS")

    def groupId(self):
        return "gaiagps"

    def shortHelpString(self):
        return self.tr(
            "Extracts .jpg/.jpeg files from a KMZ (zip) and copies them into a destination folder."
        )

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT_KMZ,
                self.tr("Input KMZ"),
                behavior=QgsProcessingParameterFile.File,
                fileFilter="KMZ (*.kmz);;All files (*.*)",
            )
        )

        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.OUTPUT_FOLDER, self.tr("Photos folder")
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.FLATTEN, self.tr("Flatten subfolders"), defaultValue=True
            )
        )

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.OVERWRITE, self.tr("Overwrite existing files"), defaultValue=False
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        kmz_path = self.parameterAsString(parameters, self.INPUT_KMZ, context)
        out_dir = self.parameterAsString(parameters, self.OUTPUT_FOLDER, context)
        flatten = self.parameterAsBool(parameters, self.FLATTEN, context)
        overwrite = self.parameterAsBool(parameters, self.OVERWRITE, context)

        if not os.path.isfile(kmz_path):
            raise QgsProcessingException(f"KMZ not found: {kmz_path}")

        os.makedirs(out_dir, exist_ok=True)

        extracted = 0
        skipped = 0

        with zipfile.ZipFile(kmz_path, "r") as z:
            members = z.namelist()
            photo_members = [
                m for m in members if m.lower().endswith((".jpg", ".jpeg"))
            ]

            if not photo_members:
                feedback.pushInfo("No .jpg/.jpeg files found inside the KMZ.")
                return {self.OUTPUT_FOLDER: out_dir}

            total = len(photo_members)

            for idx, member in enumerate(photo_members, start=1):
                if feedback.isCanceled():
                    break

                feedback.setProgress(int(idx * 100 / total))

                # If Gaia stores images under folders like "files/...", flatten keeps just the filename
                filename = os.path.basename(member) if flatten else member
                dest_path = os.path.join(out_dir, filename)

                if (not overwrite) and os.path.exists(dest_path):
                    skipped += 1
                    continue

                # ensure subdirs exist if not flatten
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)

                # stream copy (no need to extract everything)
                with z.open(member) as src, open(dest_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)

                extracted += 1

        feedback.pushInfo(f"Extracted {extracted} photo(s), skipped {skipped}.")
        return {self.OUTPUT_FOLDER: out_dir}
