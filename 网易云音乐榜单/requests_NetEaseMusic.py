import json
import math
import re

import pymysql
import requests

from urllib import parse

class NeteaseCloudMusic():
  def __init__(self):
    self.count = 1
    self.url = "https://music.163.com/discover/toplist"
    self.host = "127.0.0.1"
    self.user = "root"
    self.password = "******"
    self.db = "spider"
    self.header = {
      'Referer': 'https://music.163.com/',
      'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) \
          AppleWebKit/537.36 (KHTML, like Gecko) \
          Chrome/70.0.3538.77 Safari/537.36'
    }
    self.create_sql = '''
      CREATE TABLE NetEaseCloudMusic(ID INT NOT NULL, musicName LONGTEXT,
        playTime LONGTEXT, singers LONGTEXT)
    '''
    self.importSQL = "INSERT INTO NetEaseCloudMusic(ID, musicName, playTime, singers) \
                  VALUES (%s, %s, %s, %s)"
    

  def connect_mysql(self):
    # 连接数据库
    self.db = pymysql.connect(host=self.host, user=self.user, 
                          passwd=self.password, db=self.db)
    print("成功连接Mysql数据库")
    self.cursor = self.db.cursor()
    self.cursor.execute("DROP TABLE IF EXISTS NetEaseCloudMusic")
    self.cursor.execute(self.create_sql)


  def start_request(self, *arg):
    # 向给定的url请求数据，如果arg为空，请求原始的url，否则请求arg
    url = arg if arg else self.url
    if isinstance(url, tuple):
      # arg是元组类型
      request_url = url[0]
    else:
      request_url = url
    try:
      response = requests.get(request_url, headers=self.header)
      if response.status_code == 200:
        print("请求成功")
      return response
    except Exception as e:
      print("请求失败，失败原因：", e)
    

  def process_data(self, source_response):
    # 处理原始url的请求，提取并处理每个榜单的url
    pattern = re.compile('<p class="name"><a href="(.*?)" class="s-fc0">')
    lists_link = pattern.findall(source_response.text)
    for list_link in lists_link:
      url = parse.urljoin(self.url, list_link)
      list_response = self.start_request(url)
      json_datas = self.process_jsondata(list_response)
      self.process_musicdata(json_datas)

  def process_jsondata(self, response):
    # 提取每个榜单的json数据 
    pattern = re.compile('.*?id="song-list-pre-data".*?>(.*?)</textarea>')
    match = pattern.search(response.text)
    json_datas = json.loads(match.group(1))
    with open('data.json', 'wb') as f:
      f.write(match.group(1).encode('utf8'))
    return json_datas

  def process_musicdata(self, json_datas):
    # 处理每个榜单的json数据
    for json_data in json_datas:
      music_name = json_data.get("name")
      play_time = self.process_playtime(json_data.get("duration")/1000)
      singers = ''
      for artist in json_data.get("artists"):
        singers += '/' + artist.get("name")
      singers = singers.replace('/', '', 1)
      data = [music_name, play_time, singers]
      self.save_data(data)

  def process_playtime(self, duration):
    # 处理播放时间数据
    minutes = math.floor(duration/60)
    seconds = math.floor(duration%60)
    minutes = minutes if minutes >= 10 else '0'+str(minutes)
    seconds = seconds if seconds >= 10 else '0'+str(seconds)
    return '%s:%s' % (minutes, seconds)
    
  def save_data(self, data):
    # 保存数据到数据库
    try:
      self.cursor.execute(self.importSQL, (self.count, data[0],data[1],data[2]))
      self.db.commit()
      print("成功导入第{count}条数据".format(count=self.count))
      self.count += 1
    except Exception as e:
      print("导入数据失败，失败原因：", e)
      self.db.rollback()

if __name__ == "__main__":
  spider = NeteaseCloudMusic()
  spider.connect_mysql()
  source_response = spider.start_request()
  spider.process_data(source_response)


