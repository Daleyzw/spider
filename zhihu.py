# -*- coding:utf-8 -*-
import requests
from spider import SpiderHTML
from multiprocessing import Pool
import sys,urllib,http,os,random,re,time
from bs4 import BeautifulSoup
import json


__author__ = 'waiting'
'''
使用了第三方的类库 BeautifulSoup4，请自行安装
需要目录下的spider.py文件
运行环境：python3.4,windows7
'''
#python模拟登陆
# login_url = 'https://www.zhihu.com/signup'
# headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64)\AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.118 Safari/537.36',}
# my_post = {'redir':'https://www.zhihu.com/collection/30822111',
#     'username':'15982898124',
#     'password':'zhihu777888',
#     }
# r = requests.post(login_url, data = my_post, headers = headers)
# html = r.text
# print(html)
def login():
    url = 'http://www.zhihu.com'
    loginURL = 'http://www.zhihu.com/login/email'

    headers = {
        "User-Agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:41.0) Gecko/20100101 Firefox/41.0',
        "Referer": "http://www.zhihu.com/",
        'Host': 'www.zhihu.com',
    }

    data = {
        'username': '*',
        'password': '*',
    }
    global s
    s = requests.session()
    global xsrf
    if os.path.exists('cookiefile'):
        with open('cookiefile') as f:
            cookie = json.load(f)
        s.cookies.update(cookie)
        req1 = s.get(url, headers=headers)
        soup = BeautifulSoup(req1.text, "html.parser")
        xsrf = soup.find('input', {'name': '_xsrf', 'type': 'hidden'}).get('value')
        # 建立一个zhihu.html文件,用于验证是否登陆成功
        with open('zhihu.html', 'w') as f:
            f.write(req1.content)
    else:
        req = s.get(url, headers=headers)
        # exit(req.text)
        soup = BeautifulSoup(req.text, "html.parser")
        print(soup)
        exit()

        xsrf = soup.find('input', {'name': '_xsrf', 'type': 'hidden'}).get('value')

        data['_xsrf'] = xsrf

        timestamp = int(time.time() * 1000)
        captchaURL = 'http://www.zhihu.com/captcha.gif?=' + str(timestamp)
        print(captchaURL)

        with open('zhihucaptcha.gif', 'wb') as f:
            captchaREQ = s.get(captchaURL, headers=headers)
            f.write(captchaREQ.content)
        loginCaptcha = raw_input('input captcha:\n').strip()
        data['captcha'] = loginCaptcha
        print(data)
        loginREQ = s.post(loginURL, headers=headers, data=data)
        if not loginREQ.json()['r']:
            print(s.cookies.get_dict())
            with open('cookiefile', 'wb') as f:
                json.dump(s.cookies.get_dict(), f)
        else:
            print('login fail')
login()
exit()
#收藏夹的地址
url = 'https://www.zhihu.com/collection/30822111'  #page参数改为代码添加

#本地存放的路径,不存在会自动创建
store_path = 'E:\\zhihu\收藏夹\\会员才知道的世界'

class zhihuCollectionSpider(SpiderHTML):
	def __init__(self,pageStart, pageEnd, url):
		self._url = url
		self._pageStart = int(pageStart)
		self._pageEnd = int(pageEnd)+1
		self.downLimit = 0						#低于此赞同的答案不收录

	def start(self):
		for page in range(self._pageStart,self._pageEnd):		#收藏夹的页数
			url = self._url + '?page='+str(page)
			content = self.getUrl(url)
			questionList = content.find_all('div',class_='zm-item')
			for question in questionList:						#收藏夹的每个问题
				Qtitle = question.find('h2',class_='zm-item-title')
				if Qtitle is None:								#被和谐了
					continue

				questionStr = Qtitle.a.string
				Qurl = 'https://www.zhihu.com'+Qtitle.a['href']	#问题题目
				Qtitle = re.sub(r'[\\/:*?"<>]','#',Qtitle.a.string)			#windows文件/目录名不支持的特殊符号
				try:
					print('-----正在获取问题:'+Qtitle+'-----')		#获取到问题的链接和标题，进入抓取
				except UnicodeEncodeError:
					print(r'---问题含有特殊字符无法显示---')
				try:
					Qcontent = self.getUrl(Qurl)
				except:
					print('!!!!获取出错!!!!!')
					pass
				answerList = Qcontent.find_all('div',class_='zm-item-answer  zm-item-expanded')
				self._processAnswer(answerList,Qtitle)						#处理问题的答案
				time.sleep(5)


	def _processAnswer(self,answerList,Qtitle):
		j = 0			
		for answer in answerList:
			j = j + 1
			
			upvoted = int(answer.find('span',class_='count').string.replace('K','000')) 	#获得此答案赞同数
			if upvoted < self.downLimit:
				continue
			authorInfo = answer.find('div',class_='zm-item-answer-author-info')				#获取作者信息
			author = {'introduction':'','link':''}
			try:
				author['name'] = authorInfo.find('a',class_='author-link').string 			#获得作者的名字
				author['introduction'] = str(authorInfo.find('span',class_='bio')['title']) #获得作者的简介
				author['link'] = authorInfo.find('a',class_='author-link')['href']			
			except AttributeError:
				author['name'] = '匿名用户'+str(j)
			except TypeError:  																#简介为空的情况
				pass 																		#匿名用户没有链接

			file_name = os.path.join(store_path,Qtitle,'info',author['name']+'_info.txt')
			if os.path.exists(file_name):							#已经抓取过
				continue
	
			self.saveText(file_name,'{introduction}\r\n{link}'.format(**author))			#保存作者的信息
			print('正在获取用户`{name}`的答案'.format(**author))
			answerContent = answer.find('div',class_='zm-editable-content clearfix')
			if answerContent is None:								#被举报的用户没有答案内容
				continue
	
			imgs = answerContent.find_all('img')
			if len(imgs) == 0:										#答案没有上图
				pass
			else:
				self._getImgFromAnswer(imgs,Qtitle,**author)

	#收录图片
	def _getImgFromAnswer(self,imgs,Qtitle,**author):
		i = 0
		for img in imgs:
			if 'inline-image' in img['class']:					#不抓取知乎的小图
				continue
			i = i + 1
			imgUrl = img['src']
			extension = os.path.splitext(imgUrl)[1]
			path_name = os.path.join(store_path,Qtitle,author['name']+'_'+str(i)+extension)
			try:
				self.saveImg(imgUrl,path_name)					#捕获各种图片异常，流程不中断
			except:									
				pass
				
	#收录文字
	def _getTextFromAnswer(self):
		pass

#命令行下运行，例：zhihu.py 1 5   获取1到5页的数据
if __name__ == '__main__':
	page, limit, paramsNum= 1, 0, len(sys.argv)
	if paramsNum>=3:
		page, pageEnd = sys.argv[1], sys.argv[2]
	elif paramsNum == 2:
		page = sys.argv[1]
		pageEnd = page
	else:
		page,pageEnd = 1,1

	spider = zhihuCollectionSpider(page,pageEnd,url)
	spider.start()

