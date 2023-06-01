# from pprint import pprint
from dotenv import load_dotenv

import os 
import time
import requests

def open_t(file):
    path_t = f'D:\other\{file}'
    with open(path_t, encoding='utf-8') as f:
        return f.readline()
        
def create_file_result(file, result_data):
    current = os.getcwd()
    file_name = file
    path = os.path.join(current, file_name)
    with open(path, 'w') as f:
        f.writelines(str(result_data).replace("'",'"'))
        print(f'Файл "{file_name}" создан')


class VkUploader:
    def __init__(self, user_id, token, v):
        self.params = {'access_token': token, 'v': v}
        self.base_url = 'https://api.vk.com/method/'
        response = requests.get(f'{self.base_url}/users.get', params={'user_ids': user_id, **self.params}).json()
        if 'error' in response: 
            if response['error']['error_code'] == 5:
                print('Ошибка. Ключ vk не действителен')
                exit()
        else:
            self.user_id = response['response'][0]['id']

    def get_photo_albums_ids(self):
        photo_albums_ids_list = []
        url = f'{self.base_url}/photos.getAlbums'
        params = {'owner_id': self.user_id, **self.params}
        response = requests.get(url, params=params).json()
        if response['response']['count'] == 0:
            return [None]
        data = response['response']['items']
        for el in data:
            photo_albums_ids_list.append(str(el['id']))
        return photo_albums_ids_list

    def photo_upload(self, album_id, count=5):
        photos_list = []
        likes_list = []
        date_list = []
        for i in album_id:
            time.sleep(0.4)
            if i is None:
                continue
            else:
                url = f'{self.base_url}/photos.get'
                params = {'owner_id': self.user_id, 'album_id': i, 'extended': '1', **self.params}
                response = requests.get(url, params=params)
                data = response.json()['response']['items']
                for el in data:
                    size_dict = max(el['sizes'], key=lambda x:x['height']*x['width'])  
                    photos_list.append({'likes': el['likes']['count'], 'sizes': size_dict['type'], 'area': size_dict['width'] * size_dict['height'], 'date': el['date'], 'url': size_dict['url']})
        if count == 0:
            count = len(photos_list)        
        photos_list = sorted(photos_list, key=lambda x:x['area'], reverse=True)[0:count]
        for el in photos_list:
            likes_list.append(el['likes'])
            date_list.append(el['date'])
        return (photos_list, likes_list, date_list)
    

class YaUploader:
    def __init__(self, token):
        self.headers = {'Content-Type': 'application/json', 
                       'Authorization': f'OAuth {token}'}
        self.base_url = 'https://cloud-api.yandex.net/v1/disk/resources'
    
    def _check_token(self, response):
        if 'error' in response:
            if response['error'] == 'UnauthorizedError':
                print('Ошибка. Ключ y_disk не действителен')
                exit()

    def _progress_bar(self, steps: int, graph_count: int=20, min_v: int=0, max_v: int=100, pause: float=0.01) -> None:
        step_size = (max_v - min_v) / steps
        a = 100 / graph_count
        c = (max_v - min_v) / a
        d = graph_count
        count = min_v / a
        for i in range(0, steps + 1):
            graph = '-' * int(round(count, 10))
            print(f'\r[{graph}{" " * (graph_count - len(graph))}][{int(min_v + i * step_size)}%]', end='')
            d -= c / steps
            count += c / steps
            time.sleep(pause)
        return None

    def _create_disk_folder(self):
        url = self.base_url
        params = {'path': 'photos_backup'}
        response = requests.put(url, headers=self.headers, params=params)
        self._check_token(response.json())
        print('Папка "photos_backup" на y_disk создана')

    def _get_upload_link(self, disk_file_path):
        url = f'{self.base_url}/upload'
        params = {'path': disk_file_path, 'overwrite': 'true'}
        response = requests.get(url, headers=self.headers, params=params)
        return response.json()

    def upload_images_to_disk(self, photos_data):
        self._create_disk_folder()
        result_list = []
        # Аргументы и переменные прогресс-бара
        tb_step = 100 / len(photos_data[1])
        min_tbv = 0
        max_tbv = int(round(tb_step))
        print('Загрузка фотографий на y_disk:')
        # Загрузка фотографий на y_disk
        date_count = 1
        for i, el in enumerate(photos_data[0]):
            time.sleep(0.1)
            img_data = requests.get(el['url']).content
            if photos_data[1].count(el['likes']) and photos_data[2].count(el['date']) > 1:
                file_name = f"{el['likes']}_{el['date']}_{date_count}.jpeg"
                date_count += 1
            elif photos_data[1].count(el['likes']) > 1:
                file_name = f"{el['likes']}_{el['date']}.jpeg"
            else:
                file_name = f"{el['likes']}.jpeg"
            disk_file_path = f'photos_backup/{file_name}'
            href = self._get_upload_link(disk_file_path=disk_file_path).get('href')
            response = requests.put(href, data=img_data)
            response.raise_for_status()
            result_list.append({"file_name": file_name, "size": el['sizes']})
            # Запуск прогресс-бара для каждой итерации
            self._progress_bar(steps=30, graph_count=20, min_v=min_tbv, max_v=max_tbv, pause=0.01)
            tb_dif_round = int(100 - tb_step * (len(photos_data[1]) - i - 2))
            min_tbv = max_tbv
            max_tbv = tb_dif_round
        return result_list

if __name__ == '__main__':
    load_dotenv()
    user_name_id = input('// Введите id пользователя: ')
    token_vk = input('// Введите token_vk: ')
    token_y_disk = input('// Введите token_y_disk: ')
    # user_name_id = open_t('number.txt')
    # token_vk = open_t('t_2.txt')
    # token_y_disk = open_t('t_1.txt')
    # token_vk = os.getenv('VK_API_TOKEN')
    # token_y_disk = os.getenv('Y_DISK_API_TOKEN')
    count = abs(int(input('// Введите число загружаемых фотографий (для загрузки всех - 0): ')))

    v = os.getenv('VERSION_API_VK')
    
    vk_uploader = VkUploader(user_name_id, token_vk, v)
    photos_data = vk_uploader.photo_upload(['profile', 'wall'] + vk_uploader.get_photo_albums_ids(), count=count)

    ya_uploader = YaUploader(token_y_disk)
    result_data = ya_uploader.upload_images_to_disk(photos_data)
    
    print(f'\nОбработано {len(photos_data[1])} фотографий(я,и)')
    create_file_result('result.json', result_data)