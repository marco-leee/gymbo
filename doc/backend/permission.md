# Define Permissions

1. Arrange in three levels
   1. Role
   2. Category
   3. Action
2. Role
   1. App staff (app)
   2. Manager / Organisation Admin (organisation)
   3. Trainer (trainer)
   4. Clients (client)
3. Category
   1. All
   2. Real time pose detection
   3. Dashboard (Can only read)
   4. Organisation
   5. Exercises
   6. Assessments
   7. Clients
   8. Trainers
   9. Organisations
   10. Settings
4. Action
   1. All
   2. Create
   3. Read
   4. Update
   5. Delete
5. Format: `role:category:action` i.e. `app:all:all`

# Permission to categories

1. App staff
   1. All
2. Manager / Organisation Admin
   1. Trainers
      1. All
   2. Clients
      1. All
   3. Exercises
      1. All
   4. Assessments
      1. All
   5. Dashboard
      1. Read
   6. Real time pose detection
      1. All
   7. Settings
      1. Read, Update
3. Trainer
   1. Clients
      1. All
   2. Exercises
      1. All
   3. Assessments
      1. All
   4. Dashboard
      1. All 
   5. Real time pose detection
      1. All
   6. Settings
      1. Read, Update
4. Clients
   1. Exercises
      1. All except those associated with the trainer and assessment
   2. Assessments
      1. Read
   3. Dashboard
      1. Read
   4. Real time pose detection
      1. All
   5. Settings
      1. Read, Update