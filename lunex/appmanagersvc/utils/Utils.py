def remove_special_char(item):
    if item:
        item = item.replace("@","").replace(":","").replace(".","").replace("-","")
    return item