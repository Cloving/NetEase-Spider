# encoding=utf8

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from time import sleep
import pymysql

class NetEaseCloudMusic(object):
  def __init__(self):
    self.url = "https://music.163.com"
    self.count = 0
    self.host = "127.0.0.1"
    self.user = "root"
    self.password = "******"
    self.db = "spider"
    self.chrome_option = Options()
    self.chrome_option.add_argument('--headless')
    self.DRIVER = webdriver.Chrome(chrome_options=self.chrome_option)
    # The format string is not really a normal Python format string.
    # You must always use %s for all fields.
    self.importSQL = """INSERT INTO NetEaseCloudMusic(ID, musicName, time, singer)
              VALUES (%s, %s, %s, %s)"""

  def connect_mysql(self):
    self.db = pymysql.connect(host=self.host, 
                              user=self.user, 
                              passwd=self.password, 
                              db=self.db)
    print("成功连接Mysql数据库")
    self.cursor = self.db.cursor()
    self.cursor.execute("DROP TABLE IF EXISTS NetEaseCloudMusic")
    # 如果使用单引号，需要
    sql = '''CREATE TABLE NetEaseCloudMusic(
            ID INT NOT NULL,
            musicName LONGTEXT,
            time LONGTEXT,
            singer LONGTEXT
            )'''
    self.cursor.execute(sql)

  def jump_targetpage(self):
    # 其中 driver.get 方法会打开请求的URL，
    # WebDriver 会等待页面完全加载完成之后才会返回，
    # 即程序会等待页面的所有内容加载完成，JS渲染完毕之后才继续往下执行。
    self.DRIVER.get(self.url)
    self.DRIVER.find_element_by_xpath('//ul[@class="nav"]/li[2]').click()
    try:
      self.firstChild_iframe = self.DRIVER.find_element_by_id("g_iframe")
    except Exception as e:
      print("get mask-layer failed: ", e)
    sleep(2)
    self.DRIVER.switch_to.frame(self.firstChild_iframe)
    table = self.DRIVER.find_element_by_tag_name('table')
    self.songList = table.find_elements_by_xpath('tbody/tr')
    return self.songList

  def start_search(self, song):    
    songChildList = []
    songChildList.append(song.find_element_by_xpath('td[2]//b').get_attribute('title'))
    songChildList.append(song.find_element_by_xpath('td[3]//span[@class="u-dur "]').text)
    songChildList.append(song.find_element_by_xpath('td[last()]//span').get_attribute('title'))
    return songChildList
  
  def import_data(self, data):
    try:
      self.cursor.execute(self.importSQL, (self.count+1, data[0], data[1], data[2]))
      self.db.commit()
      self.count += 1
    except Exception as e:
      print('导入数据失败： ', e)
      self.db.rollback()


if __name__ == "__main__":
  spider = NetEaseCloudMusic()
  spider.connect_mysql()
  songList = spider.jump_targetpage()
  for song in songList:
    data = spider.start_search(song)
    print(data)
    spider.import_data(data)
  # print("成功导入" + str(self.count) + "条数据")

