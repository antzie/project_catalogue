# Item Catalogue Project
A simple website application that lists items within a variety of categories and allows users to create, update or delete items and/or categories.

Part of Udacity's Full-Stack Nanodegree programme.

Runs within Vagrant virtual environment.
## Requirements.
- Python 2.7
- [Vagrant](https://www.vagrantup.com/)
- [Virtual Box](https://www.virtualbox.org/)

### Python Libraries
Assumes the following python libraries are installed.
- flask
- sqlalchemy
- oauth2client
- httplib2
- json
- requests

## Installation
### Set Up Virtual Environment
Install
- Vagrant
- Virtual Box

Clone/Download

[fullstack-nanodegree-vm](https://github.com/udacity/fullstack-nanodegree-vm)

### Set up Application
Navigate to catalog folder of virtual machine
```
cd path/vagrant/catalog
```
Clone github repository []()
```
$ git clone https://github.com/antzie/   .git
```
## Run Application
### Launch VM
From within catalog folder run:
```
vagrant up
```
Log in to VM
```
vagrant ssh
```
Navigate to shared folder
```
cd /vagrant
```
### Run Project
```
$ python project_catalogue.py
```
### Access Project
[http://localhost:8000](http://localhost:8000/
)
## License.
See License MIT for details.
