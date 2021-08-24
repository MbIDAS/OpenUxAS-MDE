#! /bin/bash -e

rm -rf ../lmcpgen_out/*
java -Xmx2048m -jar /extra/midas/LmcpGen/dist/LmcpGen.jar -mdm "demoSer.xml" -mdmdir lib -cpp -dir "out"
