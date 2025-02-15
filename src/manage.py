import unittest
from os import getenv
from time import sleep, time
import click
from sqlalchemy.exc import OperationalError
import app.database.backup_helper as backup_helper
import app.database.db_helper as db_helper
from app import create_app, db
from app.database.model import Users
from app.mylogging import init_logging

app = create_app(getenv("FLASK_ENV", "production"))
# db.app = app # db will use app if no app_context is available
init_logging(app)


@app.shell_context_processor
def make_shell_context():
    return globals()


@app.cli.command()
@click.option("-y", "--yes", is_flag=True)
def reset(yes):
    """
    Reset all Tables to Default
    """
    if not yes:
        print(
            "This will drop all tables.\n"
            "It's extremely dangerous.\n"
            "If you are sure, please type 'YES'"
        )
        if input() != "YES":
            print("Terminated.")
            return
    db_helper.reset(env=app.config["ENV"])


@app.cli.command()
def backup():
    """
    Backup Tables
    """
    backup_helper.backup()


@app.cli.command()
def test():
    tests = unittest.TestLoader().discover("tests")
    result = unittest.TextTestRunner(verbosity=2).run(tests)

    return 0 if result.wasSuccessful() else 1


@app.cli.command(name="init_database")
def init_database():
    """
    Reset all Tables to Default if not initialized
    """
    max_try = 10
    sleep_sec = 5
    success = False
    for i in range(max_try):
        try:
            db.create_all()
        except OperationalError as e:
            print(f"Error: {e}")
            print(
                f"Failed to connect to database in try {i+1}, sleep for {sleep_sec} sec"
            )
            sleep(sleep_sec)
        else:
            success = True
            break

    if success:
        print("Database connect successfully")
    else:
        raise RuntimeError(f"Could not connect to database after {max_try} tries")

    if Users.query.count() == 0:
        reset(yes=True)


@app.cli.command(name="add_user")
def add_user():
    try:
        while True:
            username = input("帳號(學號)：")
            if username == "":
                print("帳號不可為空！")
            elif Users.username_exists(username):
                print("帳號已存在！")
            else:
                break
        while True:
            password = input("密碼：")
            if len(password) < 6:
                print("密碼須至少6碼！")
            else:
                break
        name = input("姓名：")
        admin = input("是否註冊為管理員？Y/N：")
        is_admin = admin == "Y"

        user_info = {
            "username": username,
            "password": password,
            "name": name,
            "is_admin": is_admin,
        }

        db_helper.add_users([user_info])
        print("使用者新增成功")

    except KeyboardInterrupt:
        print("\n操作取消")


def calc_time(func, *args, **kwargs):
    start = time()
    result = func(*args, **kwargs)
    end = time()
    t = round((end - start) * 1000)
    return (result, f"{t} ms")
