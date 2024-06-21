import os
import vdf
import time
import winreg
import argparse
import requests
import traceback
import subprocess
from colorama import Fore, Back, Style
import colorlog
import logging
import json
from pathlib import Path
from multiprocessing.pool import ThreadPool
from multiprocessing.dummy import Pool, Lock


lock = Lock()


def init_log():
    logger = logging.getLogger('Onekey')
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    fmt_string = '%(log_color)s[%(name)s][%(levelname)s]%(message)s'
    # black red green yellow blue purple cyan 和 white
    log_colors = {
        'DEBUG': 'white',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'purple'
        }
    fmt = colorlog.ColoredFormatter(fmt_string, log_colors=log_colors)
    stream_handler.setFormatter(fmt)
    logger.addHandler(stream_handler)
    return logger


def gen_config_file():
    default_config = {"Github_Persoal_Token": "", "Custom_Steam_Path": ""}
  
    with open('./config.json', 'w', encoding='utf-8') as f:
        json.dump(default_config, f)

    log.info('程序可能为第一次启动，请填写配置文件后重新启动程序')


def load_config():
    if not os.path.exists('./config.json'):
        gen_config_file()
    else:
        with open('./config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config
    

log = init_log()
config = load_config()


print(Fore.GREEN + ' _____   __   _   _____   _   _    _____  __    __')
print(Fore.GREEN + '/  _  \ |  \ | | | ____| | | / /  | ____| \ \  / /')
print(Fore.GREEN + '| | | | |   \| | | |__   | |/ /   | |__    \ \/ /')
print(Fore.GREEN + '| | | | | |\   | |  __|  | |\ \   |  __|    \  /')
print(Fore.GREEN + '| |_| | | | \  | | |___  | | \ \  | |___    / / ')
print(Fore.GREEN + '\_____/ |_|  \_| |_____| |_|  \_\ |_____|  /_/')
print(Style.RESET_ALL)
log.info('作者ikun0014')
log.info('本项目基于wxy1343/ManifestAutoUpdate进行修改，采用GPL V3许可证')
log.info('版本：0.0.2')
log.info('项目仓库：https://github.com/ikunshare/Onekey')
log.info('本项目完全免费，如果你在淘宝，QQ群内通过购买方式获得，赶紧回去骂商家死全家')


def get(sha, path):
    url_list = [f'https://gcore.jsdelivr.net/gh/{repo}@{sha}/{path}',
                f'https://mirror.ghproxy.com/https://raw.githubusercontent.com/{repo}/{sha}/{path}']
    retry = 3
    while retry:
        for url in url_list:
            try:
                r = requests.get(url)
                if r.status_code == 200:
                    return r.content
                else:
                    log.error(f'获取失败: {path} - 状态码: {r.status_code}')
            except requests.exceptions.ConnectionError:
                log.error(f'获取失败: {path} - 连接错误')
        retry -= 1
        log.warning(f'重试剩余次数: {retry} - {path}')
    log.error(f'超过最大重试次数: {path}')
    raise Exception(f'Failed to download: {path}')


def get_manifest(sha, path, steam_path: Path, app_id=None):
    try:
        if path.endswith('.manifest'):
            depot_cache_path = steam_path / 'depotcache'
            with lock:
                if not depot_cache_path.exists():
                    depot_cache_path.mkdir(exist_ok=True)
            save_path = depot_cache_path / path
            if save_path.exists():
                with lock:
                    log.warning(f'已存在清单: {path}')
                return
            content = get(sha, path)
            with lock:
                log.info(f'清单下载成功: {path}')
            with save_path.open('wb') as f:
                f.write(content)
        elif path == 'Key.vdf':
            content = get(sha, path)
            with lock:
                log.info(f'密钥下载成功: {path}')
            depots_config = vdf.loads(content.decode(encoding='utf-8'))
            for depot_id in depots_config['depots']:
                if stool_depot_add(depot_id, '1', depots_config['depots'][depot_id]['DecryptionKey'], app_id=app_id):
                    log.info(f'添加SteamTools Depot解锁内容成功: {depot_id}')
    except KeyboardInterrupt:
        raise
    except Exception as e:
        log.error(f'处理失败: {path} - {str(e)}')
        traceback.print_exc()
        raise
    return True


def stool_lua_gen(app_id):
    steam_path = get_steam_path()
    lua_filename = f"Onekey_unlock_Game_{app_id}.lua"
    lua_filepath = steam_path / "config" / "stplug-in" / lua_filename
    
    with lock:
        if not lua_filepath.exists():
            with open(lua_filepath, "w", encoding="utf-8") as lua_file:
                lua_file.write(f'addappid({app_id}, 1, "None")\n')
        else:
            with open(lua_filepath, "a", encoding="utf-8") as lua_file:
                lua_file.write(f'addappid({app_id}, 1, "None")\n')

    log.info('生成SteamTools解锁文件成功')
    stool_depot_add(None, None, None, app_id)
    luapacka_path = steam_path / "config" / "stplug-in" / "luapacka.exe"
    subprocess.run([str(luapacka_path), str(lua_filepath)])
    return True


def stool_depot_add(depot_id, type_, depot_key, app_id):
    steam_path = get_steam_path()
    lua_filename = f"Onekey_unlock_Depot_{app_id}.lua"
    lua_filepath = steam_path / "config" / "stplug-in" / lua_filename
    
    with lock:
        if not lua_filepath.exists():
            with open(lua_filepath, "w", encoding="utf-8") as lua_file:
                lua_file.write(f'addappid({depot_id}, {type_}, "{depot_key}")\n')
        else:
            with open(lua_filepath, "a", encoding="utf-8") as lua_file:
                lua_file.write(f'addappid({depot_id}, {type_}, "{depot_key}")\n')
        
    luapacka_path = steam_path / "config" / "stplug-in" / "luapacka.exe"
    subprocess.run([str(luapacka_path), str(lua_filepath)])
    return True


def get_steam_path():
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam')
    steam_path = Path(winreg.QueryValueEx(key, 'SteamPath')[0])
    custom_steam_path = config.get("Custom_Steam_Path", "")
    if steam_path == '':
        return custom_steam_path
    else:
        return steam_path

def check_github_api_limit(headers):
    url = 'https://api.github.com/rate_limit'
    r = requests.get(url, headers=headers)
    remain_limit = r.json()['rate']['remaining']
    use_limit = r.json()['rate']['used']
    log.info(f'已用Github请求数：{use_limit}')
    log.info(f'剩余Github请求数：{remain_limit}')
    return True

def main(app_id):
    github_token = config.get("Github_Persoal_Token", "")
    if not github_token == '':
        headers = {'Authorization': f'Bearer {github_token}'}
    else:
        headers = None
        check_github_api_limit(headers)
    url = f'https://api.github.com/repos/{repo}/branches/{app_id}'
    r = requests.get(url, headers=headers)
    if 'commit' in r.json():
        sha = r.json()['commit']['sha']
        url = r.json()['commit']['commit']['tree']['url']
        r = requests.get(url, headers=headers)
        if 'tree' in r.json():
            result_list = []
            stool_lua_gen(app_id)
            with Pool(32) as pool:
                pool: ThreadPool
                for i in r.json()['tree']:
                    result_list.append(pool.apply_async(get_manifest, (sha, i['path'], get_steam_path(), app_id)))
                try:
                    while pool._state == 'RUN':
                        if all([result.ready() for result in result_list]):
                            break
                        time.sleep(0.1)
                except KeyboardInterrupt:
                    with lock:
                        pool.terminate()
                    raise
            if all([result.successful() for result in result_list]):
                log.info(f'入库成功: {app_id}')
                return True
    log.error(f'清单下载或生成.st失败: {app_id}')
    return False


parser = argparse.ArgumentParser()
parser.add_argument('-a', '--app-id')
args = parser.parse_args()
repo = 'ManifestHub/ManifestHub'
if __name__ == '__main__':
    try:
        main(args.app_id or input('需要入库的App ID(不能有空格): '))
    except KeyboardInterrupt:
        exit()
    except Exception as e:
        log.error(f'发生错误: {str(e)}')
        traceback.print_exc()
    if not args.app_id:
        os.system('pause')
