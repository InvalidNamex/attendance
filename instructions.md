fastapi + sqlite


1- create a fast api project.

2- connect to sqlite database.


* OPEN API will be included with all endpoints

* Basic auth for all endpoint calls


Database design:

1- users table:

    - userID INTEGER PRIMARY KEY AUTOINCREMENT

    - userName TEXT NOT NULL

    - password TEXT NOT NULL

    - deviceID (optional) TEXT NOT NULL

    - isAdmin

2- settings table:

    - latitude   REAL NOT NULL

    - longitude  REAL NOT NULL

    - radius INTEGER NOT NULL DEFAULT 0

    - in_time TEXT NOT NULL

    - out_time TEXT NOT NULL


3- transactions table:

    - userID foreign key

    - timestamp

    - photo TEXT

    - stamp_type # 0= in 1= out


Endpoints:

    User endpoints:

        1- Post user create

            class UserCreate(BaseModel):

                userName: str

                password: str

                deviceID: Optional[str] = None


            class UserResponse(BaseModel):

                userID: int

                userName: str

                deviceID: Optional[str]

        

        2- user login continue..

        3- get users all continue..

        4- update user continue.. 

        5- delete

    Settings endpoints:
        post update settings
        get read settings
    
    transactions endpoints:
        post transaction:
        read all transactions with the option to filter by date range from and to, also by user, also by stamp_type (0,1)


