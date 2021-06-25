# Replaces the occurrence of value in lst with the new_value. MUST only have one occurrence of value since
# it only replaces the first instance of value
def overwrite(lst, value, new_value):
    lst[lst.index(value)] = new_value
    return lst


# Given a unicode emoji, appends it to the end of each element in the list. Unicode e.g:"\U0000274c"
def emojify_list(lst, emoji):
    return list(map(lambda x: x + f" {emoji}", lst))


# Flattens an array containing nested arrays
def flatten(nested_array):
    flattened = []
    for sublist in nested_array:
        for elem in sublist:
            flattened.append(elem)
    return flattened
