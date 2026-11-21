from sqlalchemy import inspect


def dict_to_model(data: dict, model):
    columns = {column.key for column in inspect(model).mapper.column_attrs}

    filtered_data = {key: value for key, value in data.items() if key in columns}

    return model(**filtered_data)
