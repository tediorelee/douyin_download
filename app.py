import os, re, requests, hashlib
from flask import Flask, jsonify, request
from datetime import datetime
# from tiqu_douyin import down
import time

app = Flask(__name__)

directory = "/app/Douyin" # 保存路径

douyin_API = 'http://192.168.2.166:16252'

@app.route('/')
def index():
    url = request.args.get('url')
    if not url:
        return jsonify({'message': '获取URL失败'})
    else:
        result = get_urls(url)
        return jsonify({'message': result})
    
def down(url):
    response = requests.get(f'{douyin_API}/api/hybrid/video_data?url=' + url + '&minimal=true')
    return response.json()

def fix_folder_name(folder_name):
    """
    去除不能作为文件夹名的字符
    """
    illegal_chars_regex = r'[\\/:\*\?"<>\|\n\r]'
    correct_name = re.sub(illegal_chars_regex, "", folder_name)
    # 忘了为什么
    if correct_name == '.':
        correct_name = '点'
    max_length = 70 # 最大文件名长度
    if len(correct_name) > max_length:
        correct_name = correct_name[:max_length]
    return correct_name

def get_urls(url, max_retries=10):
    retries = 0
    while retries < max_retries:
        try:
            url_result = down(url)

            # 判断是否返回了成功状态码
            if url_result.get('code') == 200:
                title = fix_folder_name(url_result['data']['desc'])
                print(title)

                # 检查是否包含图片数据，并调用相应的下载方法
                if url_result['data'].get('image_data'):
                    return down_photo(url_result, title)
                else:
                    return down_video(title, url)

            # 如果返回的不是成功状态码，处理错误信息并增加重试次数
            else:
                retries += 1
                print('解析失败，请重试', retries)
                time.sleep(1)

        except IndexError:
            print("解析过程中发生IndexError异常")
            retries += 1
            time.sleep(1)

    # 如果达到最大重试次数，返回失败信息
    print("下载失败：已达到最大重试次数")
    return '下载失败：已达到最大重试次数'


def get_file_hash(file_path):
    """
    计算文件的哈希值（MD5）
    """
    with open(file_path, 'rb') as f:
        data = f.read()
        return hashlib.md5(data).hexdigest()

def down_photo(url_result, title):
    images = url_result['data']['image_data'].get('no_watermark_image_list', [])
    current_date = datetime.now().strftime("%Y%m%d")
    directory_path = os.path.join(directory, current_date)
    os.makedirs(directory_path, exist_ok=True)

    failed_files = []
    success_files = []
    for i, image_url in enumerate(images):
        file_name = f"{title}_{i}.jpg"
        file_path = os.path.join(directory_path, file_name)
        new_hash = hashlib.md5(requests.get(image_url).content).hexdigest()
        if os.path.exists(file_path):
            current_hash = get_file_hash(file_path)
            if current_hash == new_hash:
                print(f"文件已存在且哈希值一致: {file_name}")
                continue
            else:
                while os.path.exists(file_path):
                    i += 1
                    file_name = f"{title}_{i}.jpg"
                    file_path = os.path.join(directory_path, file_name)

        response = requests.get(image_url)
        if response.status_code == 200:
            with open(file_path, 'wb') as file:
                file.write(response.content)
            print(f"保存图片成功: {file_name}")
            success_files.append(file_name)
        else:
            failed_files.append(file_name)

    if len(failed_files) > 0:
        return {"保存失败的文件": failed_files}
    elif len(success_files) > 0:
        return f'{title}:保存成功'
    else:
        return f'{title}:哈希值一致，跳过'

def down_video(title, url):
    current_date = datetime.now().strftime("%Y%m%d")
    directory_path = os.path.join(directory, current_date)
    os.makedirs(directory_path, exist_ok=True)

    try:
        file_name = f"{title}.mp4"
        file_path = os.path.join(directory_path, file_name)
        response = requests.get(douyin_API + '/api/download?url=' + url + '&prefix=true&with_watermark=true')
        if response.status_code == 200:
            with open(file_path, 'wb') as file:
                file.write(response.content)
            return f'{title}:保存成功'
        else:
            return f"保存视频失败"
    except:
        print("发生了未知错误!")


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=7818)
