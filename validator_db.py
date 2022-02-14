import json
import smtplib
import urllib.request
from datetime import datetime
import mariadb

import secrets
from logger import raw_audit_log


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

# not used
def get_validator_data(val_id: str):
    conn = connection()
    cur = conn.cursor()

    contents = urllib.request.urlopen(
            "https://sentinel.matic.network/api/v2/validators/" + str(val_id)).read()
    result = json.loads(contents)["result"]
    print(result["name"])
    command = "INSERT INTO validator_info VALUES(val_id = '" + ("val_"+(str(val_id))) + \
            "', name = '" + str(result["name"]) + \
            "', description = '" + str(max([result["description"], "null"])) + \
            "', contacts = '" + str("null") + \
            "', owner = '" + str(result["owner"]) + \
            "', signer = '" + str(result["signer"]) + \
            "', commissionPercent = '" + str(result["commissionPercent"]) + \
            "', signerPublicKey = '" + str(result["signerPublicKey"]) + \
            "', selfStake = '" + str(result["selfStake"]/1e18) + \
            "', delegatedStake = '" + str(result["delegatedStake"]/1e18) + \
            "', isInAuction = '" + str(result["isInAuction"]) + \
            "', auctionAmount = '" + str(result["auctionAmount"]) + \
            "', claimedReward = '" + str(result["claimedReward"]/1e18) + \
            "', activationEpoch = '" + str(result["activationEpoch"]) + \
            "', deactivationEpoch = '" + str(result["deactivationEpoch"]) + \
            "', jailEndEpoch = '" + str(result["jailEndEpoch"]) + \
            "', status = '" + str(result["status"]) + \
            "', contractAddress = '" + str(result["contractAddress"]) + \
            "', uptimePercent = '" + str(result["uptimePercent"]) + \
            "', delegationEnabled = '" + str(result["delegationEnabled"]) + \
            "', missedLatestCheckpointcount = '" + str(result["missedLatestCheckpointcount"]) + "');"
    print(command)
    cur.execute(command)
    conn.commit()
    conn.close()

def update_validator_data():
    conn = connection()
    cur = conn.cursor()

    for i in range(1, 140):
        contents = urllib.request.urlopen(
                "https://sentinel.matic.network/api/v2/validators/" + str(i)).read()
        result = json.loads(contents)["result"]
        name = str(result["name"]).encode("ascii", "ignore").decode() if str(result["name"]) != "None" else ("Anonymous " + str(i))
        print(name)

        command = "INSERT INTO validator_info VALUES('val_"+str(i) + \
                "', '" + str(name) + \
                "', '" + str("null") + \
                "', '" + str("null" if result["description"] is None else result["description"]) + \
                "', '" + str(result["owner"]) + \
                "', '" + str(result["signer"]) + \
                "', '" + str(result["commissionPercent"]) + \
                "', '" + str(result["signerPublicKey"]) + \
                "', '" + str(float(result["selfStake"])/1e18) + \
                "', '" + str(float(result["delegatedStake"])/1e18) + \
                "', '" + str(result["isInAuction"]) + \
                "', '" + str(result["auctionAmount"]) + \
                "', '" + str(float(result["claimedReward"])/1e18) + \
                "', '" + str(result["activationEpoch"]) + \
                "', '" + str(result["deactivationEpoch"]) + \
                "', '" + str(result["jailEndEpoch"]) + \
                "', '" + str(result["status"]) + \
                "', '" + str(result["contractAddress"]) + \
                "', '" + str(result["uptimePercent"]) + \
                "', '" + str(result["delegationEnabled"]) + \
                "', '" + str(result["missedLatestCheckpointcount"]) + "');"
        #print(command)
        cur.execute(command)
        conn.commit()
    conn.close()


def get_val_name_from_id(val_id: str):
    conn = connection()
    cur = conn.cursor()
    validator = "val_" + val_id
    command = "SELECT name FROM validator_info WHERE val_id = '" + validator + "';"
    cur.execute(command)
    result = cur.fetchall()[0][0]
    conn.close()
    return result


def get_val_contacts_from_id(val_id: str):
    conn = connection()
    cur = conn.cursor()
    validator = "val_" + val_id
    command = "SELECT contacts FROM validator_info WHERE val_id = '" + validator + "';"
    cur.execute(command)
    result = cur.fetchall()[0][0]
    conn.close()
    return result


def get_val_commission_percent_from_id(val_id: str):
    conn = connection()
    cur = conn.cursor()
    validator = "val_" + val_id
    command = "SELECT commissionPercent FROM validator_info WHERE val_id = '" + validator + "';"
    cur.execute(command)
    result = cur.fetchall()[0][0]
    conn.close()
    return result


def get_val_self_stake_from_id(val_id: str):
    conn = connection()
    cur = conn.cursor()
    validator = "val_" + val_id
    command = "SELECT selfStake FROM validator_info WHERE val_id = '" + validator + "';"
    cur.execute(command)
    result = cur.fetchall()[0][0]
    conn.close()
    return result


def get_val_delegated_stake_from_id(val_id: str):
    conn = connection()
    cur = conn.cursor()
    validator = "val_" + val_id
    command = "SELECT delegatedStake FROM validator_info WHERE val_id = '" + validator + "';"
    cur.execute(command)
    result = cur.fetchall()[0][0]
    conn.close()
    return result


def get_val_uptime_from_id(val_id: str):
    conn = connection()
    cur = conn.cursor()
    validator = "val_" + val_id
    command = "SELECT uptimePercent FROM validator_info WHERE val_id = '" + validator + "';"
    cur.execute(command)
    result = cur.fetchall()[0][0]
    conn.close()
    return result


def get_val_missed_latest_checkpoint_from_id(val_id: str):
    conn = connection()
    cur = conn.cursor()
    validator = "val_" + val_id
    command = "SELECT missedLatestCheckpointcount FROM validator_info WHERE val_id = '" + validator + "';"
    cur.execute(command)
    result = cur.fetchall()[0][0]
    conn.close()
    return result
