from doubao.browser_utils import init_browser, close_browser
from doubao.image_to_image import automate_image_upload_and_input


async def image_to_image_start(logging, image_paths, prompt, save_path,image_nums, sleep_time=70000,
                               enable_download_image=True):
    p, browser, context, page = await init_browser(logging)

    try:
        # Perform the automation
        await automate_image_upload_and_input(page, logging, image_paths, prompt, save_path, image_nums,sleep_time,
                                              enable_download_image)
    finally:
        # 关闭浏览器
        await page.close()
        await context.close()
        await close_browser(p, browser, logging)
