from datetime import datetime

import pymongo


class MongoDBConnector:
    def __init__(self, host, port):
        self.client = pymongo.MongoClient(host, port)
        self.db = self.client.default_database


class classproperty(object):
    def __init__(self, f):
        self.f = f

    def __get__(self, obj, owner):
        return self.f(owner)


class ObjectManager:
    def __init__(self, cls):
        self.cls = cls
        self.db = cls.db

    def create(self, **kwargs):
        instance = self.cls(**kwargs)
        instance_json = instance.serialize_to_json()
        instance.uuid = self.db.insert_one(instance_json).inserted_id
        return instance

    def all(self):
        return self.db.find({}, {'_id': False})

    def filter(self, **kwargs):
        return self.db.find(kwargs, {'_id': False})


class Model:
    __db_connector = MongoDBConnector("localhost", 27017)
    db_name = None

    @classproperty
    def db(cls):
        if cls.db_name is None:
            cls.db_name = cls.__name__.lower()
        return getattr(cls.__db_connector.db, cls.db_name)

    @classproperty
    def objects(cls):
        return ObjectManager(cls)

    def serialize_to_json(self):
        raise NotImplementedError("You must implement serialize_to_json")


class Department(Model):
    def __init__(self, name: str, description: str):
        self.uuid = None
        self.name = name
        self.description = description

    def serialize_to_json(self):
        return {
            "name": self.name,
            "description": self.description
        }

    def get_staff_table(self):
        pass


class Position(Model):
    def __init__(self, department: Department, rate: float):
        self.department = department
        self.rate = rate

    def serialize_to_json(self):
        return {
            'department': self.department.name,
            'rate': self.rate
        }


class Employee(Model):
    def __init__(self, *args, **kwargs):
        self.uuid = None
        self.name = kwargs.get('name', None)
        self.birth_date = kwargs.get('birth_date', None)
        self.positions = kwargs.get('positions', [])
        self.employment_date = kwargs.get('employment_date', None)
        self.snils_id = kwargs.get('snils_id', None)

    def serialize_to_json(self):
        return {
            'name': self.name,
            'birth_date': self.birth_date.timestamp(),
            'employment_date': self.employment_date.timestamp() if self.employment_date else None,
            'snils_id': self.snils_id,
            'positions': [position.serialize_to_json() for position in self.positions],
        }


if __name__ == '__main__':
    Employee.objects.create(
        name="Иванов Иван",
        birth_date=datetime(year=1997, month=4, day=30),
        snils_id=12312953444
    )

    Employee.objects.create(
        name="Андреев Андрей",
        birth_date=datetime(year=1987, month=3, day=2),
        snils_id=12312953443
    )

    emp = Employee.objects.create(
        name="Игорев Игорь",
        birth_date=datetime(year=1990, month=10, day=15),
        snils_id=12312953422
    )

    print(emp.uuid)

    print(list(Employee.objects.all()))
