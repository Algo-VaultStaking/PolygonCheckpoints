from datetime import datetime

import requests

import mariadb

import secrets

# Connect to MariaDB Platform
def connection():
    try:
        conn = mariadb.connect(
            user=secrets.MARIADB_USER,
            password=secrets.MARIADB_PASSWORD,
            host=secrets.MARIADB_HOST,
            port=3306,
            database="BlockRewards"
        )
        return conn

    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        exit()

def setup():
    conn = connection()
    cur = conn.cursor()
    cur.execute("DROP TABLE block_rewards;")

    command = "CREATE TABLE block_rewards(blockNumber INT, timestamp INT, date VARCHAR(30), blockReward DECIMAL(30,0));"
    cur.execute(command)
    cur.close()
    conn.close()

def get_block_rewards(page):
    conn = connection()
    cur = conn.cursor()

    command = "SELECT blockNumber FROM block_rewards ORDER BY blockNumber DESC LIMIT 4000;"
    cur.execute(command)
    highest_block = cur.fetchall()
    high_blocks=[]
    for j in range(len(highest_block)):
        high_blocks.append(int(highest_block[j][0]))

    response = requests.get("https://api.polygonscan.com/api"
                           "?module=account"
                           "&action=getminedblocks"
                           "&address=0x127685D6dD6683085Da4B6a041eFcef1681E5C9C"
                           "&blocktype=blocks"
                           "&page=" + str(page) +
                           "&offset=1000"
                           "&apikey=5XYPZWV3X93FZ1VHVP58VH8HZ4PWZY5BFK")
    block_list = response.json()['result']

    for block in block_list:
        if int(block["blockNumber"]) not in high_blocks:

            print(block["blockNumber"])
            dt_object = datetime.fromtimestamp(int(block["timeStamp"]))
            command = "INSERT INTO block_rewards VALUES ('" + \
                      str(block["blockNumber"]) + "', '" +\
                      str(block["timeStamp"]) + "', '" +\
                      str(dt_object) + "', '" + \
                      str(block["blockReward"]) + "');"

            cur.execute(command)
            conn.commit()
    cur.close()
    conn.close()

    return True

for i in range(1, 10):
    get_block_rewards(i)