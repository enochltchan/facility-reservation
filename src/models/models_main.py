from pydantic import BaseModel


# Model for POST request to /users
class UserModel(BaseModel):
    id: str
    password: str
    name: str
    role: str


# Model for POST request to /reservations
class ReservationModel(BaseModel):
    resource: str
    customer: str
    reserver: str
    date_time_string: str


# Model for PUT request to /reservations
class ReservationUpdateModel(BaseModel):
    serial_num: str
    resource: str
    customer: str
    reserver: str
    date_time_string: str


# Model for PUT request to /users/{id}/name
class NameModel(BaseModel):
    name: str


# Model for PUT request to /users/{id}/account_balance
class AmountModel(BaseModel):
    amount: float


# Model for PUT request to /users/{id}/activation
class ActivationModel(BaseModel):
    activation: bool


# Model for POST request to /validity
class LoginDetailsModel(BaseModel):
    id: str
    password: str


# Model for POST request to /settings/{setting}
class SettingValueModel(BaseModel):
    value: bool


# Model for POST request to /hold
class HoldModel(BaseModel):
    username: str
    password: str
    client_name: str
    request: str
    start_date: str
    start_time: str
    end_time: str
