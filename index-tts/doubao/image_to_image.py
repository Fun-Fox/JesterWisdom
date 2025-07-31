import requests
from dotenv import load_dotenv
from loguru import logger
import os

# 加载.env文件中的环境变量
load_dotenv()


async def get_picture_urls(page, image_nums=1):
    """
    获取页面中最后几个 <picture> 元素的 2x 图片链接。

    :param page: Playwright 的 page 对象
    :param image_nums: 需要获取的最后 <picture> 元素的数量
    :return: 包含所有找到的 2x 图片链接的列表
    """
    # Step 1: 定位到所有的 <picture> 元素
    await page.wait_for_timeout(3000)

    picture_elements = await page.locator('picture').all()
    if not picture_elements:
        raise Exception("未找到目标元素")

    # 根据 image_nums 取最后几个元素
    selected_pictures = picture_elements[-image_nums:]

    print(selected_pictures)
    print(len(selected_pictures))

    url_list = []

    for picture in selected_pictures:
        # Step 2: 获取 <picture> 元素内的 <source> 元素
        source_elements = await picture.locator('source').all()
        print(source_elements)
        if source_elements:
            source_element = source_elements[0]
        else:
            raise Exception("未找到目标元素")

        # Step 3: 获取 <source> 元素的 srcset 属性（图片链接）
        srcset_value = await source_element.get_attribute('srcset')

        # Step 4: 解析 srcset 属性值，提取 2x 的图像源
        if srcset_value:
            sources = srcset_value.split(',')

            # 遍历查找包含 '2x' 的项
            for source in sources:
                if '2x' in source:
                    # 提取 URL 部分（在空格之前的部分）
                    url_2x = source.strip().split(' ')[0]
                    url_list.append(url_2x)
                    break  # 找到后跳出循环

    return url_list


async def automate_image_upload_and_input(page, logging, image_paths, prompt, save_path, image_nums, sleep_time=40000,
                                          enable_download_image=True):
    if not page.is_closed():
        await page.goto("https://www.doubao.com/chat/12310316873139970")
        logging.info('页面加载完成')
        await page.wait_for_timeout(10000)  # 等待页面加载
    else:
        logging.error("页面已关闭，无法导航")
        return
    for image_path in image_paths:
        # Step 3: 选择图片，点击确认
        await page.set_input_files('input[type="file"]', image_path)

        await page.wait_for_timeout(3000)


    # Step 4: 点击输入框，输入内容
    await page.fill('textarea[data-testid="chat_input_input"]', prompt)

    # Step 5: 点击确定（假设确定按钮的类名为 confirm-button）
    await page.click('#flow-end-msg-send')

    await page.wait_for_timeout(sleep_time)

    if enable_download_image:
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                # 向下滚动页面
                logging.info('页面向下滚动')
                # 获取 scroll_view 元素
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.evaluate("window.scrollBy(0, 800)")

                scroll_view = page.locator('#chat-route-layout > div > main > div > div > div.inter-rWzItm > div > div.scroll-view-XcV8YY > div > div')
                if await scroll_view.count() > 0:
                    await scroll_view.evaluate("(element) => element.scrollTop += 800")
                await page.wait_for_timeout(3000)
                # scroll_view = page.locator('#chat-route-layout > div > main > div > div > div.inter-rWzItm > div > div[data-testid="scroll_view"]')
                # # 确保元素存在
                # if not await scroll_view.count():
                #     raise Exception("未找到 scroll_view 元素")
                # # 滚动到底部
                # await scroll_view.evaluate(
                #     "(element) => element.scrollTop = element.scrollHeight"
                # )
                # await page.wait_for_timeout(3000)  # 等待3秒
                # await scroll_view.evaluate(
                #     "(element) => element.scrollTop = element.scrollHeight"
                # )
                # 可选：等待内容加载
                await page.wait_for_timeout(3000)  # 等待3秒
                urls = await get_picture_urls(page, image_nums)
                break  # 如果成功，跳出循环
            except Exception as e:
                retry_count += 1
                logging.error(f"Error: {e}，重试次数: {retry_count}/{max_retries}")

        else:
            logging.error("达到最大重试次数，操作失败")
            return
        for idx, picture_url_2x in enumerate(urls, start=1):
            print(f"Last picture URL (2x): {picture_url_2x}")

            if picture_url_2x:
                # 使用 save_path 文件夹 + idx 命名
                await download_image(picture_url_2x, save_path, idx)


async def download_image(url, folder_path, index):
    """
    下载图片并保存到指定文件夹，使用 index 命名文件。

    :param url: 图片的 URL
    :param folder_path: 保存图片的文件夹路径
    :param index: 图片的索引，用于生成唯一文件名
    :return: 保存路径
    """
    response = requests.get(url)
    if response.status_code == 200:
        # 确保文件夹存在
        os.makedirs(folder_path, exist_ok=True)

        # 构建文件路径，使用 index 作为文件名
        file_path = os.path.join(folder_path, f"{index}.jpg")

        with open(file_path, 'wb') as f:
            f.write(response.content)
        logger.info(f"Image downloaded and saved to {file_path}")
        return file_path
    else:
        logger.error(f"Failed to download image. Status code: {response.status_code}")
        return None
