# **How to install the app**
## **For usage guidance, check the manual.pdf**

___
- ## Check if python3 is installed

```bash
python3 --version
```

- ## If it is not, run 

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3
```
___

- ## Install MySQL AND set password to 'admin'
- ## Make sure to run 'sudo mysql_secure_installation'

## [MySQL Installation](https://learnubuntu.com/install-mysql/)
___

- ## Clone the project directory

```bash
git clone git@github.com:pkrimitsas/databases.git
```

___

- ## Install the project libraries

```bash
pip install -e .
```

___

- ## Start MySQL to prepare for table creation
- ### (It will ask for password, provide 'admin' as you set while installing MySQL)

```bash
sudo mysql -u root -p
```

___

- ## Create the tables

```sql
source src/sql/schema.sql;
```

___

- ## Exit MySQL

```bash
exit;
```

___

- ## Fill the tables with randomly generated info

```bash
python3 runmefirst.py
```

___

- ## Run the app
```bash
python3 app.py
```

___

- ## Use the app

## [http://localhost:5000](http://localhost:5000/)