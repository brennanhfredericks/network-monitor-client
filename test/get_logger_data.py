import requests
import re
import concurrent.futures
import os

if not os.path.exists("remote_data"):
    os.makedirs("remote_data")


def download_file(file_url, fname):

    response = requests.get(file_url)

    assert response.status_code == 200, "file download failed"

    path = os.path.join("remote_data", fname)

    with open(path, "w+b") as fout:
        fout.write(response.content)

    return fname


def retrieve_available_files(url):
    # re expresion from stack overflow answer
    # https://stackoverflow.com/questions/499345/regular-expression-to-extract-url-from-an-html-link

    response = requests.get(url)

    assert response.status_code == 200, "get request failed"

    web_page = response.text
    files = re.findall(r'href=[\'"]?([^\'" >]+)', web_page)
    urls = [f"{url}{f}" for f in files]

    # with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executer:

        future_to_download = {
            executer.submit(download_file, url, fname): fname
            for fname, url in zip(files, urls)
        }

        for future in concurrent.futures.as_completed(future_to_download):
            try:
                data = future.result()
            except Exception as exc:
                print("generated an exception: %s" % exc)
            else:
                print(f"completed {data}")

    # print(urls[0])


if __name__ == "__main__":

    retrieve_available_files("http://192.168.88.40:8000/")
