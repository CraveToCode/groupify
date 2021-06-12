def overwrite(lst, value, new_value):
    for index, name in enumerate(lst):
        if value in lst:
            lst[index] = new_value
    return lst
