# SecureShed

## Central Controller

### Creating A Database For Central Controller

The central database uses sqlite3, which you will need to install (see dependencies).

To create the central controller database called ccontroller.db:

1. Change to the central controller directory: secureshed/central_controller
2. Create using:  sqlite3 controller.db < ../../databases/CentralController.sql
3. Open the database using: sqlite3 controller.db
4. Run the following query to create default keycode (last param is to identify
   the entry as a master code):  INSERT INTO KeyCodes VALUES(null, '1234', true);
5. Quit sqllite3: .quit
