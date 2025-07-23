import os


def create_dir_if_doesnt_exists(spider_name, directory):
    new_path = directory
    if not os.path.exists(new_path):
        os.makedirs(new_path)
        print(f"'{new_path}' created!")
