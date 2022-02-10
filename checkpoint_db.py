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


def orig():
    conn = connection()
    cur = conn.cursor()

    for i in range(1, 140):
        contents = urllib.request.urlopen(
                "https://sentinel.matic.network/api/v2/validators/" + str(i)).read()
        result = json.loads(contents)["result"]
        print(result["name"])
        command = "INSERT INTO validator_info VALUES(val_id = '" + ("val_"+(str(i))) + \
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

def load_validator_data():
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


def update_contacts():
    validator_names = {
        1: ["Matic Foundation Node 1", "<@464476646599032842>, <@716728038414614609>"],
        2: ["Matic Foundation Node 2", "<@464476646599032842>, <@716728038414614609>"],
        3: ["Matic Foundation Node 3", "<@464476646599032842>, <@716728038414614609>"],
        4: ["Matic Foundation Node 4", "<@464476646599032842>, <@716728038414614609>"],
        5: ["Matic Foundation Node 5", "<@464476646599032842>, <@716728038414614609>"],
        6: ["Matic Foundation Node 6", "<@464476646599032842>, <@716728038414614609>"],
        7: ["Matic Foundation Node 7", "<@464476646599032842>, <@716728038414614609>"],
        8: ["Torus Validator", "<@154627664722788353>"],
        9: ["Infosys", "Infosys Team"],
        10: ["Chain Guardians", "Chain Guardians Team"],
        11: ["Biconomy Validator", "<@653545381635817482>"],
        12: ["AutoMATIC Generator", "<@374951910991724544>"],
        13: ["Decentral.games", "<@643537106504777738>"],
        14: ["Node A-Team", "<@827001438618124311>, <@752535399964082329>"],  # <@526799690730045440>,
        15: ["AUDIT.one", "<@705774216670216192>"],
        16: ["BCW Technologies", "<@707807163736653834>"],
        17: ["FreshMATIC 17", "<@298470233872662528>"],
        18: ["Sapien", "<@785551937348173884>"],
        19: ["Ethermon Validator", "Ethermon Team"],
        20: ["Blockops", "<@400012724484046848>"],
        21: ["Polyient", "Polyient Team"],
        22: ["Wetez", "<@649520475415773185>"],
        23: ["YieldWallet.io", "<@588284266236870658>"],
        24: ["IGGalaxy 24", "IGGalaxy Team"],
        25: ["Validation Capital", "<@144238060660326401>, <@539886204548808717>"],
        26: ["Newroad Network", "<@603296132197646391>"],
        27: ["Bi23 Labs", "<@470054080820150272>"],
        28: ["WolfEdge Capital", "<@388086793637199873>"],
        29: ["Stake Capital", "Stake Capital Team"],
        30: ["Staking4All", "<@556857416243871769>"],
        31: ["AnkrValidator", "<@411566789252874241>"],
        32: ["StakePool", "<@675037249385267221>"],
        33: ["StakePower", "StakePower Team"],
        34: ["HashQuark", "<@745836457742041209>"],
        35: ["Octopos", "Octopos Team"],
        36: ["algo|stake", "<@427159114133536783>"],
        37: ["Vault Staking", "<@712863455467667526>"],
        38: ["Creol Carbon Neutral Validator", "<@114583345337204740>"],
        39: ["MobiFi Validator", "<@480890054797950986>"],
        40: ["Smart Stake", "<@400514913505640451>"],
        41: ["Mind Heart Soul", "<@560638192223649792>"],
        42: ["Cryptonomicon", "<@450681845441363988>"],
        43: ["MANTRA DAO", "<@757419888443785276>, <@315290836042645505>"],
        44: ["Shut down", "shut down"],
        45: ["Pathrocknetwork", "<@394870302691295234>"],
        46: ["AverageGuy", "Average Guy"],
        47: ["Ownest", "<@298210402884517888>"],
        48: ["Proton", "<@475361536857079819>"],
        49: ["Oceanblock Validator", "<@740574903375495210>"],
        50: ["Witval", "<@611195855151693825>"],
        51: ["Mosc", "Mosc Team"],
        52: ["Borrow718", "Borrow718 Team"],
        53: ["Pool to the Moon", "Pool Team"],
        54: ["NinjaNodes", "<@702246720049905695>"],
        55: ["SolidStake", "<@753069488538386444>"],
        56: ["ERM", "ERM Team"],
        57: ["Bit Cat", "Bit Cat Team"],
        58: ["V1", "<@836857263259385856>"],
        59: ["Tessellated Geometry", "<@403811901613670401>"],
        60: ["Power", "Power Team"],
        61: ["Bondly Matic Node", "Bondly Matic Node Team"],
        62: ["Stake.Works", "<@464840045224919041>"],
        63: ["Bountyblok", "<@384851086520877056>, <@117461209883738121>"],
        64: ["DSRV", "<@601237877569093637>, <@854633327033057280>"],
        65: ["Niche Networks", "<@111007386507948032>"],
        66: ["Masternode24", "<@551955825422499854>"],
        67: ["ledhed2222", "Ledhed Team"],
        68: ["Chainflow", "<@448904762885144576>"],
        69: ["lux8.net", "<@342623737905938433>"],
        70: ["infStones", "<@778483510645227530>"],
        71: ["Test01", "test team"],
        72: ["Web3Nodes Validator", "<@208466097836392448>"],
        73: ["Darth Vader", "<@500243158299443200>"],
        74: ["Maj Loves Reg", "Maj"],
        75: ["kytzu", "<@377743001000083466>"],
        76: ["Making.cash", "<@391116246810230785>"],
        77: ["Everstake", "<@542737604307845121>"],
        78: ["RADAR Staking 78", "<@430257814972268544>, <@384052398391558175>"],
        79: ["Matrix", "<@781901805315424297>"],
        80: ["RADAR Staking 80", "<@430257814972268544>, <@384052398391558175>"],
        81: ["IGGalaxy 81", "IGGalaxy Team"],
        82: ["FieryDev-MCLB", "<@388086793637199873>"],
        83: ["Anchor Staking 83", "<@671211783926710272>"],
        84: ["Test01 84", "Test team"],
        85: ["Coinstash", "<@705056036507353088>"],
        86: ["DeFiMatic", "<@408769213948231680>"],
        87: ["chainvibes", "<@333580184630460416>"],
        88: ["Staked", "<@831191726458142820>, <@400012724484046848>"],
        89: ["Bodega-Matic 89", "<@468512583943716864>"],
        90: ["AlwaysUp365", "AlwaysUp365 Team"],
        91: ["Anonymous 91", "Team"],
        92: ["Anonymous 92", "Team"],  # <@682569032116862976>
        93: ["Anonymous 93", "Team"],
        94: ["Anonymous 94", "Team"],
        95: ["Tavis Digital", "<@872474191662809128>"],
        96: ["MaticStaking.com", "MaticStaking Team"],
        97: ["Binance Node", "Binance"],  # <@804294696665874462>
        98: ["Proton Gaming", "<@448146837887516685>"],
        99: ["Double Jump.tokyo", "<@281717054543888385>"],
        100: ["PrideVel", "<@811573459301171220>, <@869545150051913778>"],
        101: ["MyContainer.com", "My Container Team"],
        102: ["Nobi", "<@558147565129039882>"],
        103: ["Anchor Staking 103", "<@671211783926710272>"],
        104: ["SNZ Pool", "<@509723150477688834>"],
        105: ["Bodega-Matic", "<@468512583943716864>"],
        106: ["METAops | Matic1", "<@592972419745185802>"],
        107: ["Anon Low Fee", "<@240179945274474496>"],
        108: ["Bware Labs", "<@827848971677990973>"],
        109: ["Just-Mining", "<@645907810420260885>"],
        110: ["AllNodes", "<@377191973385404417>"],
        111: ["Hounddog Streaming", "<@633105096476983309>"],
        112: ["Anonymous 112", "Team"],
        113: ["Anonymous 113", "Team"],
        114: ["VK Labs", "<@798637468714532884>"],
        115: ["PMCapital", "PMCapital Team"],
        116: ["Blocks United", "<@479302211621355522>, <@657736472216076318>"],
        117: ["Ideas Unplugged", "<@740476162580414482>"],
        118: ["Diversified Validator Network", "<@817020448369541191>"],
        119: ["Polygon millionaires", "Polygon Millionaires Team"],
        120: ["FreshMATIC.net", "<@298470233872662528>"],
        121: ["Stakin", "<@537373173461811230>"],
        122: ["Abyss Finance", "Abyss Team"],
        123: ["Stake.fish", "<@604121911340826648>, <@890966691557826561>"],
        124: ["Polymon", "<@390259509681192981>"],
        125: ["Perfect Stake", "Perfect Stake Team"],
        126: ["Valis Labs", "Valis Labs Teams"],
        127: ["Supermoon", "Supermoon Team"],
        128: ["SelfLiquidity", "SelfLiquidity Team"],
        129: ["IGGalaxy 129", "IGGalaxy"],
        130: ["The Abyss", "The Abyss Team"],
        131: ["VC Capital", "VC Capital Team"],
        132: ["Fahrenheit", "Fahrenheit Team"],
        133: ["Anonymous 133", "Team"],
        134: ["Prometheus Pool", "Prometheus Pool Team"],
        135: ["Anonymous 135", "Team"]

    }
    conn = connection()
    cur = conn.cursor()
    for key in validator_names.keys():
        validator = "val_" + str(key)
        command = "UPDATE validator_info " \
                  "SET contacts = '" + validator_names[key][1] + "' " \
                  "WHERE val_id = '" + validator + "';"
        cur.execute(command)
        conn.commit()

    conn.close()
