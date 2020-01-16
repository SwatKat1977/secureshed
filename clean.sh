# Clean top-level directory.
rm -rf .DS_Store

# Clean top-level source directory.
rm -rf src/.DS_Store

# Clean central controller directory.
rm -rf src/centralController/__pycache__
rm -rf src/centralController/.DS_Store
rm -rf src/centralController/DeviceTypes/__pycache__
rm -rf src/centralController/DeviceTypes/.DS_Store

# Clean keypad controller directory.
rm -rf src/KeypadController/__pycache__
rm -rf src/KeypadController/.DS_Store
rm -rf src/KeypadController/Gui/__pycache__

rm -rf src/common/__pycache__
rm -rf src/common/.DS_Store
rm -rf src/common/APIClient/__pycache__
rm -rf src/common/APIClient/.DS_Store

rm -rf src/APIs/__pycache__
rm -rf src/APIs/.DS_Store
rm -rf src/APIs/Keypad/__pycache__
rm -rf src/APIs/Keypad/.DS_Store