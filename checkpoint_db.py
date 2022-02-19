import json
import smtplib
import urllib.request
from datetime import datetime
import mariadb

import secrets
from logger import raw_audit_log
## https://sentinel.matic.network/swagger/#/

# Connect to MariaDB Platform
def connection():
    try:
        conn = mariadb.connect(
            user=secrets.MARIADB_USER,
            password=secrets.MARIADB_PASSWORD,
            host=secrets.MARIADB_HOST,
            port=3306,
            database="checkpoints"
        )

        return conn


    except mariadb.Error as e:
        raw_audit_log(f"Error connecting to MariaDB Platform: {e}")
        exit()


def initial_setup():
    try:
        conn = connection()
        cur = conn.cursor()
        cur.execute("DROP TABLE checkpoint_status;")
        cur.execute("DROP TABLE validator_info;")

        command = "CREATE TABLE checkpoint_status(checkpoint_num INT, date VARCHAR(30), "
        for i in range(1, 151):
            command = command + "val_" + str(i) + " INT, "

        command = command[:-2] + ");"
        cur.execute(command)

        cur.execute("CREATE TABLE validator_info(val_id VARCHAR(10), "
                    "name VARCHAR(50), "
                    "contacts VARCHAR(200), "
                    "description varchar(1000), "
                    "owner VARCHAR(50), "
                    "signer VARCHAR(50), "
                    "commissionPercent FLOAT(10,4), "
                    "signerPublicKey VARCHAR(150), "
                    "selfStake BIGINT, "
                    "delegatedStake BIGINT, "
                    "isInAuction VARCHAR(10), "
                    "auctionAmount BIGINT, "
                    "claimedReward BIGINT, "
                    "activationEpoch INT, "
                    "deactivationEpoch INT, "
                    "jailEndEpoch INT, "
                    "status VARCHAR(50), "
                    "contractAddress VARCHAR(50), "
                    "uptimePercent FLOAT(10,4), "
                    "delegationEnabled VARCHAR(10), "
                    "missedLatestCheckpointcount INT);")

        cur.close()
        conn.close()
    except mariadb.Error as e:
        raw_audit_log(f"Error: {e}")


def load_checkpoint_data(checkpoint: int):
    conn = connection()
    cur = conn.cursor()

    command = "INSERT INTO checkpoint_status VALUES ("+str(checkpoint)+", '2/4/22 00:00:00', "
    for i in range(1, 151):
        command = command + "val_" + str(100) + ", "

    command = command[:-2] + ");"
    cur.execute(command)
    conn.commit()
    conn.close()

#    contents = urllib.request.urlopen(
#        "https://sentinel.matic.network/api/v2/validators/" + str(index) + "/checkpoints-signed").read()
#    estimated_checkpoints.append(json.loads(contents)["result"][0]["checkpointNumber"])

def get_latest_saved_checkpoint():
    conn = connection()
    cur = conn.cursor()
    cur.execute("SELECT MAX(checkpoint_num) FROM checkpoint_status;")
    result = cur.fetchall()[0][0]
    conn.close()
    return result


def get_last_validator_checkpoint(val_id: str):
    conn = connection()
    cur = conn.cursor()
    validator = "val_" + val_id
    cur.execute("SELECT MAX(" + validator + ") FROM checkpoint_status;")
    result = cur.fetchall()[0][0]
    conn.close()
    return result


def set_new_checkpoint(checkpoint: str):
    conn = connection()
    cur = conn.cursor()

    command = "INSERT INTO checkpoint_status VALUES (" + checkpoint + ", '" + str(datetime.now()) + "', "
    for i in range(1, 151):
        command = command + "Null, "

    command = command[:-2] + ");"

    cur.execute(command)
    conn.commit()
    conn.close()


def update_validator_checkpoint(val_id: str, checkpoint: str):
    conn = connection()
    cur = conn.cursor()
    validator = "val_" + val_id
    command = "UPDATE checkpoint_status " \
              "SET " + validator + " = " + checkpoint + \
              " WHERE checkpoint_num = (SELECT MAX(checkpoint_num) FROM checkpoint_status);"
    cur.execute(command)
    conn.commit()
    conn.close()
    return True


# Send email
def send_email(current_checkpoint, validator_checkpoint):
    gmail_user = secrets.gmail_user
    gmail_password = secrets.gmail_password

    sent_from = secrets.gmail_user
    to = [secrets.to]

    if current_checkpoint - validator_checkpoint == 0:
        body = "Successful Checkpoint: " + str(current_checkpoint)
    else:
        body = "MISSING Checkpoint: " + str(current_checkpoint) + ", yours is " + str(validator_checkpoint)

    email_text = """From: Vault Staking
To: User
Subject: New Checkpoint\n
""" + body

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)
        server.sendmail(sent_from, to, email_text)
        server.close()

        raw_audit_log("Email sent!")
    except Exception as ex:
        raw_audit_log(str(ex))
