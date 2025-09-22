
def increment_id(last_id):
    prefix = ''.join(filter(str.isalpha, last_id))
    number = ''.join(filter(str.isdigit, last_id))
    if not number:
        number = "0"
    new_number = str(int(number) + 1).zfill(len(number))
    return f"{prefix}{new_number}"



