from playwright.sync_api import sync_playwright
import time
import os
import requests
import multiprocessing
import subprocess
import shutil

def get_driver():
    path = os.path.join(os.getcwd(), "browser_data")
    p = sync_playwright().start()
    browser = p.chromium.launch_persistent_context(path, headless=False, viewport={"width": 1920, "height": 1080}, args=['--window-size=1920,1080'])
    page = browser.pages[0]
    page = browser.new_page()
    return page


def download_file(link, number):
    r = requests.get(link, stream=True)
    with open(f"ts_files/{number}.ts", "wb") as f:
        f.write(r.content)

def download_file_2(link, number):
    r = requests.get(link, stream=True)
    with open(f"ts_files_2/{number}.ts", "wb") as f:
        f.write(r.content)


def split_list(l, n):
    k, m = divmod(len(l), n)
    return (l[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n))


def get_audio(link):
    try:
        os.mkdir("ts_files")
    except:
        pass
    # each link contains a .m3u8 file that has our links and a key
    r = requests.get(link)
    with open("current_file.m3u8", "wb") as f:
        f.write(r.content)
    # read it and save the key first
    with open("current_file.m3u8", "r") as f:
        lines = f.readlines()
        for line in lines:
            if "URI=" in line:
                key = line.split("URI=\"")[1].split("\"")[0]
    # download the key
    r = requests.get(key)
    with open("key.bin", "wb") as f:
        f.write(r.content)
    # download all urls from it as ts files, also decrypt them separately
    no = 0
    links = []
    with open("current_file.m3u8", "r") as f:
        lines = f.readlines()
        for line in lines:
            if "hmac" in line:
                links.append(line.strip())
    # now donwload 5 files at a time
    for i in range(0, len(links), 10):
        processes = []
        for j in range(i, min(i+10, len(links))):
            p = multiprocessing.Process(target=download_file, args=(links[j], j, ))
            processes.append(p)
            p.start()
        for p in processes:
            p.join()

    # now create another.m3u8 file that has all the ts files
    with open("current_file.m3u8", "r") as f:
        lines = f.readlines()
        final_data = ""
        num = 0
        with open("all_files.m3u8", "w") as f2:
            for line in lines:
                if "URI" in line:
                    final_data += '#EXT-X-KEY:METHOD=AES-128,URI="key.bin",' + line.split(",")[-1]
                elif "hmac" not in line:
                    final_data += line + ""
                else:
                    final_data += f"ts_files/{num}.ts\n"
                    num += 1
            f2.write(final_data)
    # if the file exists then delete it
    if os.path.exists("audio.aac"):
        os.remove("audio.aac")
    subprocess.call("ffmpeg -y -allowed_extensions ALL -i all_files.m3u8 -c copy audio.aac")

def get_video(link):
    try:
        os.mkdir("ts_files_2")
    except:
        pass
    # each link contains a .m3u8 file that has our links and a key
    r = requests.get(link)
    with open("current_file.m3u8", "wb") as f:
        f.write(r.content)
    # read it and save the key first
    with open("current_file.m3u8", "r") as f:
        lines = f.readlines()
        for line in lines:
            if "URI=" in line:
                key = line.split("URI=\"")[1].split("\"")[0]
    # download the key
    r = requests.get(key)
    with open("key.bin", "wb") as f:
        f.write(r.content)
    # download all urls from it as ts files, also decrypt them separately
    no = 0
    links = []
    with open("current_file.m3u8", "r") as f:
        lines = f.readlines()
        for line in lines:
            if "hmac" in line:
                links.append(line.strip())
    # donwload 5 files at a time using multiprocessing
    for i in range(0, len(links), 10):
        processes = []
        for j in range(i, min(i+10, len(links))):
            p = multiprocessing.Process(target=download_file_2, args=(links[j], j, ))
            processes.append(p)
            p.start()
        for p in processes:
            p.join()
    # now create another.m3u8 file that has all the ts files
    with open("current_file.m3u8", "r") as f:
        lines = f.readlines()
        final_data = ""
        num = 0
        with open("all_files.m3u8", "w") as f2:
            for line in lines:
                if "URI" in line:
                    final_data += '#EXT-X-KEY:METHOD=AES-128,URI="key.bin",' + line.split(",")[-1]
                elif "hmac" not in line:
                    final_data += line + ""
                else:
                    final_data += f"ts_files_2/{num}.ts\n"
                    num += 1
            f2.write(final_data)
    # if the file exists then delete it
    if os.path.exists("video.mkv"):
        os.remove("video.mkv")
    # if the file exists then overwrite it
    subprocess.call(f"ffmpeg -y -allowed_extensions ALL -i all_files.m3u8 -c copy video.mkv")


def login(page):

    url = "https://yanfaa.com/us/home"
    page.goto(url)
    time.sleep(2)
    page.reload()
    time.sleep(4)
    #find ul with class="inline-list account list" and then find the second li
    page.click("ul.inline-list.account.list li:nth-child(2)", timeout=5000)
    time.sleep(2)
    #id="loginInputEmail"
    page.type("#loginInputEmail", email)
    #id="loginInputPassword"
    page.type("#loginInputPassword", password)
    #click on the login button
    # class = "cta-button cta-button-primary"
    time.sleep(2)
    page.click(".cta-button.cta-button-primary")
    time.sleep(200)

# def extract_links(page):
#     page.goto("https://yanfaa.com/us/home")
#     # now find all div with class="swiper-slide"
#     time.sleep(5)
#     divs = page.query_selector_all("div.swiper-slide")
#     # form there get the a tag and then get the href
#     links = []
#     for div in divs:
#         links.append(div.query_selector("a").get_attribute("href"))
#     return links


def extract_video_links(base_url, link, page):
    url = base_url + link
    page.goto(url)
    time.sleep(5)
    # scroll to below and try to find a button, if it is there then click on it again, if not then break
    # scroll to the bottom
    if os.path.exists(f"{link.split('/')[-1]}.txt") == False:
        all_links = []
        while True:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            try:
                #get all buttons
                x = False
                buttons = page.query_selector_all("button")
                # find the one with class="cta-button cta-button-primary"
                for button in buttons:
                    #text= المزيد من الكورسات 
                    if button.get_attribute("class") == "cta-button cta-button-primary" and "المزيد من الكورسات"  in button.text_content():
                        button.click()
                        x = True
                        break
                if x == False:
                    break
                time.sleep(2)
            except:
                break
        # find all divs class="course_card"
        divs = page.query_selector_all("div.course-widget")
        # get the a tag above it and then get the href
        for div in divs:
            all_links.append(div.query_selector("a").get_attribute("href"))
        with open(f"{link.split('/')[-1]}.txt", "w") as f:
            for link in all_links:
                f.write(link + "\n")                    
    else:
        print("Already processed...")


def split_list(l, n):
    k, m = divmod(len(l), n)
    return (l[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n))


def get_fastly_token(video_id):
    url = f"https://edge.api.brightcove.com/playback/v1/accounts/6164421959001/videos/{video_id}"
    headers = {
        "Accept": "application/json;pk=BCpkADawqM39gu-OwrCa_hliNP-JNlirsPbpkgzVVdhNh2XkQPdKa03XkZXfnIpf2c1O-PPck3OnXLzqXt5tQoRW71jvg7YxMqmTSWFKDLPJh1C3V1c_Pjd4DjKCGCJtunclR8sPdNl2y5Wz9llrsjeu9quSyjcBHallLX_--xrEuZFiaFmOHjoGK3_4I3jG5iRdQqIXfxHxmG63i3gDjuOotuGmeoSslOO6NktkTGQBnxUK1G0J7SvDloVvSoNLa-mwZmMNg1tkqXUTcBDTPPtL63RweCmwV9KB4KJKClPae3nml2nRHjhLiQVeOaTpeVwbcUyt8AHAC1TCbQU-ST5ohGeJKc3xTBnqTJhZLDzmlB0aETMhbdM8b3mEov-zG24iJ_8wS842cqUP",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://yanfaa.com",
        "Referer": "https://yanfaa.com/",
        "Sec-Ch-Ua": '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    }

    r = requests.get(url, headers=headers)
    token = r.json()["sources"][0]["src"].split("=")[1]
    uri_id = r.json()["poster"].split("/main/")[0].split("/")[-1]
    video_id = r.json()["poster"].split("/"+uri_id)[0].split("/")[-1]
    return token, uri_id, video_id


def get_master_file(video_id, uri_id, fastly_token):
    url = f"https://manifest.prod.boltdns.net/manifest/v1/hls/v4/aes128/{video_id}/{uri_id}/10s/master.m3u8?fastly_token={fastly_token}"
    # open the above url in a browser and download the .m3u8 file

    headers = {
        "authority": "manifest.prod.boltdns.net",
        "method": "GET",
        "path": f"/manifest/v1/hls/v4/aes128/{video_id}/{uri_id}/10s/master.m3u8?fastly_token={fastly_token}",
        "scheme": "https",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://yanfaa.com",
        "Referer": "https://yanfaa.com/",
        "Sec-Ch-Ua": "\"Google Chrome\";v=\"117\", \"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"117\"",
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": "\"Windows\"",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
    }

    r = requests.get(url, headers=headers, json={"fastly_token":fastly_token})
    # save the .m3u8 file
    with open("master.m3u8", "w") as f:
        f.write(r.text)


def download_video(page_link, page, directory):
    url = base_url + page_link
    page.goto(url)
    time.sleep(2)
    page.reload()
    time.sleep(4)
    videos_list = page.query_selector_all("div.video_list")[0]
    # get all the li tags
    li_tags = videos_list.query_selector_all("li")
    for li_tag in li_tags:
        if __name__ == "__main__":
            #click on the li tag
            li_tag.click()
            # in li_tag get the div class="row" and in it get the first div and get its text
            video_name = li_tag.query_selector("div.row div").text_content()
            time.sleep(5)
            # find the video id
            video_id = page.query_selector("video-js").get_attribute("data-video-id")
            # in the video-js tag get the video tag and then get the poster attribute and then split it by /main/ and then get the first part and then split it by / and get the first part
            token,uri_id,video_id = get_fastly_token(video_id)
            # now get the m3u8 file
            get_master_file(video_id, uri_id, token)
            # read it and then get the URI= links
            uris = []
            uris_2 = []
            with open("master.m3u8", "r") as f:
                lines = f.readlines()
                for line in lines:
                    if "URI=" in line:
                        uris.append(line.split("URI=\"")[1].split("\"")[0])
                for line in lines:
                    if "rendition" in line:
                        uris_2.append(line.strip())
            audio_link = uris[0]
            get_audio(audio_link)
            get_video(uris_2[-3])
            # remove the ts_files and ts_files_2 folders
            shutil.rmtree("ts_files")
            shutil.rmtree("ts_files_2")
            # now merge audio and video and output mp4 and then move it to the directory
            video_name = video_name.replace(" ", "_")
            # if the file exists then overwrite it
            subprocess.call(f"ffmpeg -y -i video.mkv -i audio.aac -c copy {video_name}.mp4")
            # now move the file to the directory
            try:
                os.rename(f"{video_name}.mp4", f"{directory}/{video_name}.mp4")
            except:
                pass        


base_url = "https://yanfaa.com"
def main():
    main_driver = get_driver()
    try:
        login(main_driver)
    except:
        print("Maybe already logged in...")
    print("Logged in...")
    links =['/us/category/Design', '/us/category/Marketing', '/us/category/IT', '/us/category/Business', '/us/category/Photo_Film', '/us/category/Content', '/us/category/MotionGraphics', '/us/category/Languages', '/us/category/edutainment', '/us/category/HR', '/us/category/Crafts']
    if os.path.exists("processed.txt") == False:
        with open("processed.txt", "w") as f:
            f.write("")

    for link in links:
        if link in open("processed.txt", "r").read():
            continue
        try:
            os.mkdir(link.split("/")[-1])
        except:
            pass
        extract_video_links(base_url, link, main_driver)
        # now download the videos
        course_links = open(f"{link.split('/')[-1]}.txt", "r").read().split("\n")
        course_links = [link for link in course_links if link != ""]
        for course_link in course_links:
            if os.path.exists("processed_courses.txt") == False:
                with open("processed_courses.txt", "w") as f:
                    f.write("")
            if course_link in open("processed_courses.txt", "r").read():
                continue
            try:
                os.mkdir(f"{link.split('/')[-1]}/{course_link.split('/')[-1]}")
            except:
                pass
            download_video(course_link, main_driver, f"{link.split('/')[-1]}/{course_link.split('/')[-1]}")
            with open("processed_courses.txt", "a") as f:
                f.write(course_link + "\n")
        with open("processed.txt", "a") as f:
            f.write(link + "\n")

if __name__ == "__main__":
    main()