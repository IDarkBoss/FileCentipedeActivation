import datetime, os, sys, time, traceback, pyperclip
from bs4 import BeautifulSoup
from sqlalchemy import Column, create_engine, DateTime, String, Integer
from sqlalchemy.orm import declarative_base, sessionmaker
import httpx

dbpath = r"MyDatabase.db"
url = "https://filecxx.com/zh_CN/activation_code.html"
today = time.strftime("%Y-%m-%d", time.localtime())
now = datetime.datetime.now()
Base = declarative_base()


def resource_path(relative_path):
    """
    获取程序中所需文件资源的绝对路径
    """

    try:
        # PyInstaller创建临时文件夹,将路径存储于_MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def getSqliteSession():
    exist = os.path.exists(resource_path(dbpath))
    if exist:
        engine = create_engine(r"sqlite:///" + dbpath)
        DBSession = sessionmaker(bind=engine)
        return DBSession()
    else:
        raise RuntimeError("不存在db文件")


dbSession = getSqliteSession()


class ActivateCode(Base):
    """
    表结构
    """

    # 表的名字:
    __tablename__ = "FILECXX_ACTIVATE_CODE"

    # 表的结构:
    id = Column(Integer(), primary_key=True)
    START_TIME = Column(DateTime())
    END_TIME = Column(DateTime())
    CODE = Column(String(200))

    def __init__(self, START_TIME, END_TIME, CODE):
        self.START_TIME = START_TIME
        self.END_TIME = END_TIME
        self.CODE = CODE


def queryData() -> ActivateCode:
    """
    从数据库中查询数据
    return: 激活码
    """
    return (
        dbSession.query(ActivateCode)
        .filter(ActivateCode.START_TIME <= now)
        .filter(ActivateCode.END_TIME >= now)
        .first()
    )


def deleteData():
    """
    清空数据
    """
    dbSession.query(ActivateCode).delete()


def saveData(START_TIME, END_TIME, CODE):
    """
    保存数据
    """
    new_code = ActivateCode(START_TIME=START_TIME, END_TIME=END_TIME, CODE=CODE)
    dbSession.add(new_code)
    dbSession.commit()


def getPage():
    """
    获取网页
    """
    r = httpx.get(url, timeout=10)
    return r.text


def parserHtml():
    """
    解析网页
    """
    page = getPage()
    codes = BeautifulSoup(page, features="html.parser").find(id="codes")
    codeList = str(codes).split("\n")

    for i in range(len(codeList)):
        string = codeList[i]

        if " - " in string:
            dates = string.split(" - ")
            startTime = datetime.datetime.strptime(dates[0], "%Y-%m-%d %H:%M:%S")
            endTime = datetime.datetime.strptime(dates[1], "%Y-%m-%d %H:%M:%S")
            codeText = codeList[i + 1]
            saveData(startTime, endTime, codeText)
    
    print("已完成激活码爬取")


def startProgram():
    """
    开始程序
    """
    code = queryData()
    if code is None:
        print("没找到激活码，开始爬取")
        deleteData()
        parserHtml()
        code = queryData()
    print("找到激活码")
    pyperclip.copy(code.CODE)
    print("复制成功")


if __name__ == "__main__":
    try:
        startProgram()
        time.sleep(1)
        exit(0)
    except Exception:
        print(traceback.format_exc())
        time.sleep(30)
        exit(1)
