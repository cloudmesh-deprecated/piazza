#!/bin/bash


echo "Installing the MongoDB Binaries ..."
brew install mongodb

echo "Creating /data/db directory"
sudo mkdir -p /data/db

echo "Complete"
