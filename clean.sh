# Clean top-level directory.
rm -rf .DS_Store

# Clean top-level source directory.
rm -rf src/.DS_Store

# Clean central controller directory.
rm -rf src/centralController/__pycache__
rm -rf src/centralController/.DS_Store
rm -rf src/centralController/keypadAPI/__pycache__
rm -rf src/centralController/keypadAPI/.DS_Store

# Clean control panel directory.
rm -rf src/keypadController/__pycache__
rm -rf src/keypadController/.DS_Store

rm -rf src/common/__pycache__
rm -rf src/common/.DS_Store
rm -rf src/common/APIClient/__pycache__
rm -rf src/common/APIClient/.DS_Store

rm -rf src/APIs/__pycache__
rm -rf src/APIs/.DS_Store
rm -rf src/APIs/Keypad/__pycache__
rm -rf src/APIs/Keypad/.DS_Store