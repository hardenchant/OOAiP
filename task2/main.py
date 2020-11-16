from datetime import datetime

import pymongo
from bson.objectid import ObjectId


class MongoDBConnector:
    def __init__(self, host, port):
        self.client = pymongo.MongoClient(host, port)
        self.db = self.client.default_database


class classproperty(object):
    def __init__(self, f):
        self.f = f

    def __get__(self, obj, cls):
        return self.f(cls)


class QuerySet:
    def __init__(self, object_manager, filter_query, result):
        self.object_manager = object_manager
        self.filter_query = filter_query
        self.result = result

    def __repr__(self):
        return self.result

    def __getitem__(self, key):
        return self.object_manager.model_cls(**self.result[key])

    def update(self, **kwargs):
        return self.object_manager.db.update_many(self.filter_query, {'$set': kwargs})

    def delete(self):
        return self.object_manager.db.delete_many(self.filter_query)


class ObjectManager:
    def __init__(self, model_cls):
        self.model_cls = model_cls
        self.db = model_cls.db

    def create(self, **kwargs):
        instance = self.model_cls(**kwargs)
        instance_json = instance._serialize_to_json()
        instance.uuid = self.db.insert_one(instance_json).inserted_id
        return instance

    def all(self):
        return self.filter()

    def filter(self, **kwargs):
        if 'uuid' in kwargs:
            kwargs['_id'] = ObjectId(kwargs.pop('uuid'))
        return QuerySet(self, kwargs, self.db.find(kwargs))


class Model:
    __db_connector = MongoDBConnector("localhost", 27017)
    __object_manager = ObjectManager
    db_name = None

    def __init__(self, *args, **kwargs):
        self.uuid = kwargs.get('uuid', kwargs.get('_id', None))

    @classproperty
    def db(cls):
        if cls.db_name is None:
            cls.db_name = cls.__name__.lower()
        return getattr(cls.__db_connector.db, cls.db_name)

    @classproperty
    def objects(cls):
        return cls.__object_manager(cls)

    def _serialize_to_json(self):
        raise NotImplementedError("You must implement _serialize_to_json")

    def _is_object_exists_in_db(self):
        return bool(self.uuid)


class Department(Model):
    def __init__(self, name: str, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.description = kwargs.get('description', None)

    def __repr__(self):
        return f'{self.name} ({self.description or "Описание отсутствует"})'

    def _serialize_to_json(self):
        return {
            "name": self.name,
            "description": self.description
        }

    def get_staff_table(self):
        pass


class Employee(Model):
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.name = kwargs.get('name', None)
        self.birth_date = kwargs.get('birth_date', None)
        self.employment_date = kwargs.get('employment_date', None)
        self.snils_id = kwargs.get('snils_id', None)

    def __repr__(self):
        return f'{self.snils_id}: {self.name} ({datetime.fromtimestamp(self.birth_date)})'

    def _serialize_to_json(self):
        return {
            'name': self.name,
            'birth_date': self.birth_date.timestamp(),
            'employment_date': self.employment_date.timestamp() if self.employment_date else None,
            'snils_id': self.snils_id,
        }

    @property
    def positions(self):
        return [
            (
                Department.objects.filter(uuid=pos.department)[0],
                pos.rate
            ) for pos in Position.objects.filter(employee=self.uuid)
        ]

    @positions.setter
    def positions(self, value: list):
        if not self._is_object_exists_in_db():
            raise Exception('Object not saved to db')
        Position.objects.filter(employee=self.uuid).delete()
        for (dep, rate) in value:
            Position.objects.create(employee=self, department=dep, rate=rate)


class Position(Model):
    def __init__(self, department: Department, employee: Employee, rate: float, **kwargs):
        super().__init__(**kwargs)
        self.department = department
        self.employee = employee
        self.rate = rate

    def _serialize_to_json(self):
        return {
            'department': self.department.uuid,
            'employee': self.employee.uuid,
            'rate': self.rate
        }


if __name__ == '__main__':
    # You can see main operations below with examples

    # Drop db
    Department.objects.all().delete()
    Employee.objects.all().delete()
    Position.objects.all().delete()

    # Employee creation, full data, part data
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

    Employee.objects.create(
        name="Игорев Игорь",
        birth_date=datetime(year=1990, month=10, day=15),
        snils_id=12312953422
    )

    # Print each Employee from db
    print(list(Employee.objects.all()))

    # Search employee in db by name
    print(list(Employee.objects.filter(name="Андреев Андрей")))
    # Search employee in db by snils
    print(list(Employee.objects.filter(snils_id=12312953443)))

    # Update Employee info with search by snils
    Employee.objects.filter(snils_id=12312953443).update(name="Вася Пупкин")
    print(list(Employee.objects.filter(snils_id=12312953443)))

    # Delete Employee info with search by snils
    Employee.objects.filter(snils_id=12312953443).delete()
    print(list(Employee.objects.all()))

    # ================================================

    # Department creation, full data, part data
    Department.objects.create(
        name='Бухгалтерия',
        description='В этом отделе происходит обработка финансовых документов'
    )
    Department.objects.create(
        name='Безопасность'
    )
    Department.objects.create(
        name='HR'
    )
    # Print each Department from db
    print(list(Department.objects.all()))

    # Update Department with search by name
    Department.objects.filter(name='Безопасность').update(
        description='В этом отделе проводится проверка новых сотрудников'
    )
    print(list(Department.objects.all()))

    # Update Department with search by name
    Department.objects.filter(name='Бухгалтерия').delete()
    print(list(Department.objects.all()))

    # ================================================

    # Set Departments for Employee
    emp = Employee.objects.all()[0]
    dep1 = Department.objects.all()[0]
    dep2 = Department.objects.all()[1]
    print(emp, dep1, dep2)

    emp.positions = [
        (dep1, 0.5),
        (dep2, 0.5),
    ]

    # Get Departments for Employee
    print(emp.positions)
