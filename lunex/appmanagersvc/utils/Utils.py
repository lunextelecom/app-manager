from string import lower
def remove_special_char(item):
    if item:
        item = item.replace(".","").replace("-","")
        item = item.replace("@",".").replace(":","_")
        
    return lower(item)