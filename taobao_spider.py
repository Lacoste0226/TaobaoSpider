import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from urllib import request

from lxml import etree

class TaobaoSpider:

    def __init__(self):
        chrome_options = webdriver.ChromeOptions()
        # 不加载图片，加快访问速度
        # chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
        # 设置为开发者模式，避免被识别
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        self.web_driver = webdriver.Chrome(options=chrome_options)
        self.web_driver_wait = WebDriverWait(self.web_driver,30)

        self.url = 'https://login.taobao.com/member/login.jhtml'
        self.username = '淘宝账号'
        self.password = '淘宝密码'
        self.all_picture_url = []
        self.count = 0

    def login(self):
        self.web_driver.get(self.url)

        # 设置selenium为全屏界面，避免出现滑块
        self.web_driver.maximize_window()

        try:
            # 切换为帐号密码登录
            login_method_switch = self.web_driver_wait.until(
                expected_conditions.presence_of_element_located((By.XPATH, '//*[@id="J_QRCodeLogin"]/div[5]/a[1]')))
            login_method_switch.click()

            # 找到用户名输入框并输入
            username_input = self.web_driver_wait.until(
                expected_conditions.presence_of_element_located((By.ID, 'TPL_username_1')))
            username_input.send_keys(self.username)

            # 找到密码输入框并输入
            password_input = self.web_driver_wait.until(
                expected_conditions.presence_of_element_located((By.ID, 'TPL_password_1')))
            password_input.send_keys(self.password)

            # 找到登录按钮并点击
            login_button = self.web_driver_wait.until(
                expected_conditions.presence_of_element_located((By.XPATH, '//*[@id="J_SubmitStatic"]')))
            login_button.click()
            #
            # 找到名字标签并打印内容
            taobao_name_tag = self.web_driver_wait.until(expected_conditions.presence_of_element_located(
                (By.XPATH, '//*[@id="J_Col_Main"]/div/div[1]/div/div[1]/div[1]/div/div[1]/a/em')))
            print(f"登陆成功：{taobao_name_tag.text}")

            # 休息5秒钟，然后关闭浏览器
            time.sleep(5)
            # self.web_driver.close()
        except Exception as e:
            print(e)
            self.web_driver.close()
            print("登陆失败")

    def shopping_car(self):
        # 找到购物车地址并点击
        shopping_car = self.web_driver_wait.until(expected_conditions.presence_of_element_located((By.ID, 'mc-menu-hd')))
        shopping_car.click()

    def shopping_url(self):
        # 进入想要爬取的商品地址
        shopping_url = self.web_driver_wait.until(expected_conditions.presence_of_all_elements_located((By.XPATH,'//*[@id="J_Item_1050164571727"]/ul/li[2]/div/div[2]/div[1]/a')))
        shopping_url[0].click()

    def login_comments(self):
        # 获取当前所有句柄（窗口）
        all_handles = self.web_driver.window_handles
        # 切换到新的窗口
        self.web_driver.switch_to.window(all_handles[1])
        # 拉取显示全部页面，以加载商品评论
        self.web_driver.execute_script(
            'window.scrollTo(0, document.body.scrollHeight)'
        )
        # 点击商品评论
        shopping_comments = self.web_driver_wait.until(expected_conditions.presence_of_all_elements_located((By.XPATH,'//*[@id="J_TabBar"]/li[2]')))
        shopping_comments[0].click()
        # 点击图片评论
        picture_comments_list = self.web_driver_wait.until(expected_conditions.presence_of_all_elements_located((By.XPATH,'//*[@class="rate-list-picture rate-radio-group"]')))
        picture_comments_list[0].click()

        # 获取评论图片
        time.sleep(3)
        self.get_picture_comments(self.web_driver)

    # 分析当前页面源码
    def parse_html(self,web_driver,xpath_bds):
        html = web_driver.page_source
        xpath_parse_html = etree.HTML(html)
        shopping_picture_list = xpath_parse_html.xpath(xpath_bds)
        return shopping_picture_list

    # 获取当前页所有图片评论地址
    def get_picture_comments(self,web_driver):
        xpath_bds = '//*[@id="J_Reviews"]/div/div[6]/table/tbody//img/@src'
        shopping_picture_list = self.parse_html(web_driver,xpath_bds)

        # 清理列表，除去空字符串并加入到大列表中
        shopping_picture_list = list(filter(None, shopping_picture_list))
        self.all_picture_url.extend(shopping_picture_list)
        # 判断是否还有下一页
        self.next_page(web_driver)

    # 浏览器下拉至下一页节点处
    def plush_next_page(self,web_dirver):
        target = web_dirver.find_element_by_xpath('//*[@id="J_Reviews"]/div/div[6]/table/tbody/tr[20]')
        web_dirver.execute_script("arguments[0].scrollIntoView();", target)

    # 判断是否还有下一页   //*[@id="J_Reviews"]/div/div[7]/div/a
    def next_page(self,web_driver):
        self.plush_next_page(web_driver)
        time.sleep(2)
        next_page_bds = '//*[@id="J_Reviews"]/div/div[7]/div/a/text()'
        page_list = self.parse_html(web_driver,next_page_bds)
        for i in page_list:
            print(i)
        if '下一页>>' in page_list:
            next_page_list = self.web_driver_wait.until(expected_conditions.presence_of_all_elements_located(
                (By.XPATH, '//a[text()="下一页>>"]')))
            time.sleep(5)
            next_page_list[0].click()
            self.get_picture_comments(web_driver)
        else:
            print('已经是最后一页了')

    def save_picture(self):
        for picture_url in self.all_picture_url:
            self.count += 1
            big_picture_url = "https:"+picture_url.replace("40x40","400x400")
            print(big_picture_url)
            # 下载图片到本地
            request.urlretrieve(big_picture_url,'D:\spider_code\desk_picture\{}.jpg'.format(self.count))
        print(self.count)

    def main(self):
        self.login()
        self.shopping_car()
        self.shopping_url()
        self.login_comments()
        self.save_picture()

if __name__ == "__main__":
    spider = TaobaoSpider()
    spider.main()