# Replaces the occurrence of value in lst with the new_value. MUST only have one occurrence of value since
# it only replaces the first instance of value
def overwrite(lst, value, new_value):
    lst[lst.index(value)] = new_value
    return lst
