#!/bin/bash

get_key(){
    echo "Getting public key for package management system ..."
    
	apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10
}

create_list_file(){
    echo "Creating list file ..."
    
    release=$(lsb_release -sc)
    echo "deb http://repo.mongodb.org/apt/ubuntu $release/mongodb-org/3.2 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.2.list
 
}

update(){
    echo "Update package lists ..."
    
    sudo apt-get update
}

install_mongo(){
    echo "Installing latest MongoDB package ...."
    
    sudo apt-get install -y mongodb-org --allow-unauthenticated
}

create_piazza_directory(){
    echo "Creating piazza directory in home ..."
    mkdir ~/piazza
}

create_data_directory(){
    echo "Creating data directory in piazza ..."
    mkdir -p ~/piazza/data
}

create_list_file

update

install_mongo

create_data_directory

echo "Complete."
