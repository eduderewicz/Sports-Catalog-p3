Project 3 - This is a basic favorite players list that a group of users could compile... 
Perhaps the groups allstar picks by sport. 
A user must create a sport and positions (this user becomes the sole manager of that sport and positions). 
Once at least one position exists for a sport, any logged in user may begin adding players. 

This project uses Python, the flask framework, and a SQLite database

Note to mimic my exact setup: install vagrant and virtual box - https://www.udacity.com/wiki/ud088/vagrant

once vagrant and virtual box are installed

start vagrant  
`vagrant up`

ssh into vagrant  
`vagrant ssh`   

clone repo:  
`git clone https://github.com/eduderewicz/Sports-Catalog-p3.git`  

CD into directory 

Run the following commands to create the database   
`python database_setup.py` 

populate with some sample data  
`python lotsofsports.py` 

run the project   
`python project.py`

access the project via web browser  
`http://localhost:5000/`

