#!/bin/bash

echo "Entered bash file..."
echo "Opening NavigationTestSimulator.cxx..."
echo "WPI port number: $1"
echo "WPI IP/hostname: $2"
echo "SNR port number: $3"
echo "SNR IP/hostname: $4"
echo "Running NavigationTestSimulator.cxx with command: $5"

$5 $1 $2 $3 $4

exit