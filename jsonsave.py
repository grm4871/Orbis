import json

def save_list(lst,filename):
    """
    Saves list to filename
    """
    data = []
    for element in lst:
        data.append(element.output_data())
    with open(filename, 'w+') as file:
        file.write(json.dumps(data))

def save_lst(lst,filename):
    """
    Saves list to filename WITHOUT OUTPUT_DATA()
    """
    data = []
    for element in lst:
        data.append(element)
    with open(filename, 'w+') as file:
        file.write(json.dumps(data))

def load_list(filename):
    """
    Returns newly created list from filename
    """
    try:
        with open(filename, 'r') as file:
            return json.loads(file.read())
    except:
        with open(filename, 'w+') as file:
            file.write(json.dumps([]))
        return []

def save_dict(dict,filename):
    """
    Saves dict to filename
    """
    file.write(json.dumps(dict))

def load_dict(filename):
    """
    Returns newly created dict from filename
    """
    try:
        with open(filename, 'r') as file:
            return json.loads(file.read())
    except:
        with open(filename, 'w+') as file:
            file.write(json.dumps({}))
        return {}