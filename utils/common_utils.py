import uuid


def generate_record_id(prefix=""):
    src_id = str(uuid.uuid1())
    sub_id = "".join(src_id.split("-"))
    return prefix+sub_id


if __name__ == '__main__':
    print(len(generate_record_id('PJ')))