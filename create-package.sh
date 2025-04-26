rm leechdetector.zip
zip -r leechdetector.zip leechdetector/* -x "__pycache__/*"
zip leechdetector.zip manifest.json
zip leechdetector.zip __init__.py