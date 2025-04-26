rm leechdetector.zip
cd leechdetector
zip -r ../leechdetector.zip * -x "__pycache__/*"
cd ..
zip leechdetector.zip manifest.json
