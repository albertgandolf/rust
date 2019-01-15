# -*- coding: utf-8 -*-
import operator
from peewee import _ModelQueryHelper, Node

def __parse_field_name(str):
    pos = str.find('__')
    if pos == -1:
        return str, None
    else:
        return str[:pos], str[pos:]

@Node.copy
def dj_where(self, *expressions):
    if self._where is not None:
        expressions = (self._where,) + expressions
    self._where = reduce(operator.and_, expressions)

def django_where_returns_clone(func):

    def inner(self, *args, **kwargs):
        fields = self.model._meta.fields
        args = []
        for field_name, value in kwargs.items():
            field_name, op = __parse_field_name(field_name)
            db_field = fields.get(field_name, None)
            if not db_field and field_name.endswith('_id'):
                # maybe it's a foreign key
                field_name = field_name[:-3]
                db_field = fields.get(field_name, None)

            if not op:
                args.append(db_field.__eq__(value))
            else:
                if op == '__not':
                    args.append(db_field.__ne__(value))
                elif op == '__lt':
                    args.append(db_field.__lt__(value))
                elif op == '__lte':
                    args.append(db_field.__le__(value))
                elif op == '__gt':
                    args.append(db_field.__gt__(value))
                elif op == '__gte':
                    args.append(db_field.__ge__(value))
                elif op == '__notin':
                    if len(value) > 0:
                        args.append(db_field.not_in(value))
                elif op == '__icontains':
                    args.append(db_field.contains(value))
                elif op == '__range':
                    args.append(db_field.between(value[0], value[1]))
                elif op == '__in':
                    if len(value) == 0:
                        # TODO2: handle situations like "select * from table where id in ()"
                        value = ['-98765']
                    args.append(db_field.in_(value))
        kwargs = {}
        clone = self.clone()  # Assumes object implements `clone`.
        func(clone, *args, **kwargs)
        return clone

    inner.call_local = func  # Provide a way to call without cloning.
    return inner

_ModelQueryHelper.dj_where = django_where_returns_clone(dj_where)

print ('peewee hacked: dj_where func attached on ModelSelect')