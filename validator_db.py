import datetime
import json
import urllib.request
import mariadb

import secrets
from logger import raw_audit_log


# Connect to MariaDB Platform
def get_db_connection():
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


def update_validator_data(db_connection, val_id: str):
    conn = db_connection
    cur = conn.cursor()
    val_id = str(val_id)
    message = ""
    try:
        contents = urllib.request.urlopen(
                "https://sentinel.matic.network/api/v2/validators/" + str(val_id)).read()
        result = json.loads(contents)["result"]

        name = str(result["name"]).encode("ascii", "ignore").decode() \
            if (str(result["name"]) != "None" and str(result["name"]) != "") \
            else ("Anonymous " + str(val_id))
        owner = str(result["owner"])
        signer = str(result["signer"])
        commission = float(result["commissionPercent"])
        selfStake = max(int(result["selfStake"]), get_val_self_stake_from_id(conn, val_id))
        delegatedStake = int(result["delegatedStake"])
        # str(result["isInAuction"])
        # str(result["auctionAmount"])
        activation = int(result["activationEpoch"])
        deactivation = int(result["deactivationEpoch"])

        if name != get_val_name_from_id(conn, val_id):
            message += "**Name**: `" + get_val_name_from_id(conn, val_id) + "` is now `" + name + "`.\n"

        if owner != get_val_owner_from_id(conn, val_id):
            message += "**Owner Address**: `" + get_val_name_from_id(conn, val_id) + "` changed owner address from `" + \
                       get_val_owner_from_id(conn, val_id) + "` to `" + owner + "`.\n"

        if signer != get_val_signer_from_id(conn, val_id):
            message += "**Signer Address**: `" + get_val_name_from_id(conn, val_id) + "` changed signer address from `" + \
                       get_val_signer_from_id(conn, val_id) + "` to `" + owner + "`.\n"

        if commission != get_val_commission_percent_from_id(conn, val_id):
            message += "**Commission**: `" + get_val_name_from_id(conn, val_id) + "` changed commission from `" + \
                       str(get_val_commission_percent_from_id(conn, val_id)) + "` to `" + str(commission) + "`.\n"

        if selfStake > get_val_self_stake_from_id(conn, val_id):
            message += "**Self Stake**: `" + get_val_name_from_id(conn, val_id) + "` changed self stake from `" + \
                       str("{:,.2f}".format(float(get_val_self_stake_from_id(conn, val_id))/1e18)) + "` to `" + str("{:,.2f}".format(float(selfStake)/1e18)) + "`.\n"

        if abs(delegatedStake - get_val_delegated_stake_from_id(conn, val_id)) >= 5000000000000000000000000:
            message += "**Delegated Stake**: `" + get_val_name_from_id(conn, val_id) + "`'s delegated stake changed from `" + \
                      str("{:,.2f}".format(float(get_val_delegated_stake_from_id(conn, val_id))/1e18)) + "` to `" + str("{:,.2f}".format(delegatedStake/1e18)) + "`.\n"

        if activation != get_val_activation_from_id(conn, val_id):
            message += "**Activation**: `" + str(get_val_name_from_id(conn, val_id)) + "` is now active from checkpoint `" + str(activation) + "`.\n"

        if deactivation != get_val_deactivation_from_id(conn, val_id):
            message += "**Unbond**: `" + str(get_val_name_from_id(conn, val_id)) + "` has unbonded effective checkpoint `" + str(deactivation) + "`. cc: <@712863455467667526> \n"

        command = "UPDATE validator_info " \
                  "SET name = '" + name + \
                "', owner = '" + owner + \
                "', signer = '" + signer + \
                "', commissionPercent = '" + str(commission) + \
                "', signerPublicKey = '" + str(result["signerPublicKey"]) + \
                "', selfStake = '" + str(selfStake) + \
                "', delegatedStake = '" + str(delegatedStake) + \
                "', claimedReward = '" + str(result["claimedReward"]) + \
                "', activationEpoch = '" + str(activation) + \
                "', deactivationEpoch = '" + str(deactivation) + \
                "', jailEndEpoch = '" + str(result["jailEndEpoch"]) + \
                "', status = '" + str(result["status"]) + \
                "', contractAddress = '" + str(result["contractAddress"]) + \
                "', uptimePercent = '" + str(result["uptimePercent"]) + \
                "', delegationEnabled = '" + str(result["delegationEnabled"]) + \
                "', missedLatestCheckpointcount = '" + str(result["missedLatestCheckpointcount"]) + \
                "' WHERE val_id = 'val_" + val_id + "';"

    #    "', description = '" + str(max([result["description"], "null"])) + \
        cur.execute(command)
        conn.commit()
    except Exception as e:
        print("Error in val_db: " + str(e))
        pass

    return message[:-2]


def get_val_name_from_id(db_connection, val_id: str):
    conn = db_connection
    cur = conn.cursor()
    validator = "val_" + val_id
    command = "SELECT name FROM validator_info WHERE val_id = '" + validator + "';"
    try:
        cur.execute(command)
        result = cur.fetchall()[0][0]
    except:
        result = ""
    return result


def get_val_contacts_from_id(db_connection, val_id: str):
    conn = db_connection
    cur = conn.cursor()
    validator = "val_" + val_id
    command = "SELECT contacts FROM validator_info WHERE val_id = '" + validator + "';"
    try:
        cur.execute(command)
        result = cur.fetchall()[0][0]
    except:
        result = ""
    return result


def set_val_contacts_from_id(db_connection, val_id: str, contacts: str):
    conn = db_connection
    cur = conn.cursor()
    contacts = get_val_contacts_from_id(conn, val_id) + ", " + contacts
    validator = "val_" + val_id
    command = "UPDATE validator_info " \
              "SET contacts = '" + str(contacts) + \
              "' WHERE val_id = '" + validator + "';"
    cur.execute(command)
    conn.commit()
    

def remove_val_contacts_from_id(db_connection, val_id: str, user: str):
    conn = db_connection
    cur = conn.cursor()
    contacts = str(get_val_contacts_from_id(conn, val_id)).split(", ")
    if user in contacts:
        contacts.remove(user)

    validator = "val_" + val_id
    command = "UPDATE validator_info " \
              "SET contacts = '" + str(", ".join(contacts)) + \
              "' WHERE val_id = '" + validator + "';"
    cur.execute(command)
    conn.commit()
    
    return None


def get_val_commission_percent_from_id(db_connection, val_id: str):
    conn = db_connection
    cur = conn.cursor()
    validator = "val_" + val_id
    command = "SELECT commissionPercent FROM validator_info WHERE val_id = '" + validator + "';"
    try:
        cur.execute(command)
        result = cur.fetchall()[0][0]
    except:
        result = ""
    
    return result


def get_val_owner_from_id(db_connection, val_id):
    conn = db_connection
    cur = conn.cursor()
    validator = "val_" + val_id
    command = "SELECT owner FROM validator_info WHERE val_id = '" + validator + "';"
    try:
        cur.execute(command)
        result = cur.fetchall()[0][0]
    except:
        result = ""
    
    return result


def get_val_signer_from_id(db_connection, val_id):
    conn = db_connection
    cur = conn.cursor()
    validator = "val_" + val_id
    command = "SELECT signer FROM validator_info WHERE val_id = '" + validator + "';"
    try:
        cur.execute(command)
        result = cur.fetchall()[0][0]
    except:
        result = ""
    
    return result


def get_val_self_stake_from_id(db_connection, val_id: str):
    conn = db_connection
    cur = conn.cursor()
    validator = "val_" + val_id
    command = "SELECT selfStake FROM validator_info WHERE val_id = '" + validator + "';"
    try:
        cur.execute(command)
        result = cur.fetchall()[0][0]
    except:
        result = 0.0
    
    return int(result)


def get_val_delegated_stake_from_id(db_connection, val_id: str):
    conn = db_connection
    cur = conn.cursor()
    validator = "val_" + val_id
    command = "SELECT delegatedStake FROM validator_info WHERE val_id = '" + validator + "';"
    try:
        cur.execute(command)
        result = cur.fetchall()[0][0]
    except:
        result = 0.0
    
    return int(result)


def get_val_uptime_from_id(db_connection, val_id: str):
    conn = db_connection
    cur = conn.cursor()
    validator = "val_" + val_id
    command = "SELECT uptimePercent FROM validator_info WHERE val_id = '" + validator + "';"
    try:
        cur.execute(command)
        result = cur.fetchall()[0][0]
    except:
        result = 0
    
    return float(result)


def get_val_missed_latest_checkpoint_from_id(db_connection, val_id: str):
    conn = db_connection
    cur = conn.cursor()
    validator = "val_" + val_id
    command = "SELECT missedLatestCheckpointcount FROM validator_info WHERE val_id = '" + validator + "';"
    try:
        cur.execute(command)
        result = cur.fetchall()[0][0]
    except:
        result = ""
    
    return result


def get_val_activation_from_id(db_connection, val_id):
    conn = db_connection
    cur = conn.cursor()
    validator = "val_" + val_id
    command = "SELECT activationEpoch FROM validator_info WHERE val_id = '" + validator + "';"
    try:
        cur.execute(command)
        result = cur.fetchall()[0][0]
    except:
        result = ""
    
    return int(result)


def get_val_deactivation_from_id(db_connection, val_id):
    conn = db_connection
    cur = conn.cursor()
    validator = "val_" + val_id
    command = "SELECT deactivationEpoch FROM validator_info WHERE val_id = '" + validator + "';"
    try:
        cur.execute(command)
        result = cur.fetchall()[0][0]
    except:
        result = ""
    
    return int(result)


def get_val_status_from_id(db_connection, val_id):
    conn = db_connection
    cur = conn.cursor()
    validator = "val_" + val_id
    command = "SELECT status FROM validator_info WHERE val_id = '" + validator + "';"
    try:
        cur.execute(command)
        result = cur.fetchall()[0][0]
    except:
        result = ""

    return result
