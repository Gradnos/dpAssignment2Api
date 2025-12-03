# HOW TO USE 

### setup
`poetry install`

### run
 - Default(In Memory) `poetry run uvicorn main:app --reload`

 - Using SQL 
 `USE_SQLITE=true poetry run uvicorn main:app --reload`

 - SQL + Custom DB Path `USE_SQLITE=true DB_PATH=my_habits.db poetry run uvicorn main:app --reload`


