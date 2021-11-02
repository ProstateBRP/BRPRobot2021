REM bat file to run  NavigationTestSimulator.cxx on Windows OS

@echo off 
echo %1
echo %2
echo %3
echo %4
echo %5

echo "Entered bash file..."
echo "Opening NavigationTestSimulator.cxx..."
echo "WPI port number: %1"
echo "WPI IP/hostname: %2"
echo "SNR port number: %3"
echo "SNR IP/hostname: %4"
echo "Running NavigationTestSimulator.cxx with command: %5"

%5 %1 %2 %3 %4
pause